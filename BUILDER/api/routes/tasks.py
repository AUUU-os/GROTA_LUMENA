"""
Task CRUD + dispatch endpoints.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from BUILDER.api import models as m
from BUILDER.api.routes.ws import broadcast

logger = logging.getLogger("builder.api.tasks")
router = APIRouter(tags=["tasks"])


def _get_state():
    from BUILDER.api.app import tasks, dispatcher, audit, registry
    from BUILDER.api.app import ollama_bridge, claude_bridge, codex_bridge, gemini_bridge
    return tasks, dispatcher, audit, registry, ollama_bridge, claude_bridge, codex_bridge, gemini_bridge


@router.post("/tasks", response_model=m.TaskResponse)
async def create_task(body: m.TaskCreate):
    tasks, dispatcher, audit, *_ = _get_state()
    task = tasks.create(body.title, body.description, body.priority)
    if body.assigned_to:
        tasks.assign(task.id, body.assigned_to)
    audit.log("task_create", task_id=task.id, details=body.title)
    await broadcast("task_create", task.to_dict())
    return m.TaskResponse(**task.to_dict())


@router.get("/tasks", response_model=list[m.TaskResponse])
async def list_tasks(status: str | None = None, agent: str | None = None):
    tasks, *_ = _get_state()
    result = tasks.list(status=status, agent=agent)
    return [m.TaskResponse(**t.to_dict()) for t in result]


@router.get("/tasks/{task_id}", response_model=m.TaskResponse)
async def get_task(task_id: str):
    tasks, *_ = _get_state()
    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return m.TaskResponse(**task.to_dict())


@router.put("/tasks/{task_id}", response_model=m.TaskResponse)
async def update_task(task_id: str, body: m.TaskUpdate):
    tasks, _, audit, *_ = _get_state()
    updates = body.model_dump(exclude_none=True)
    task = tasks.update(task_id, **updates)
    if not task:
        raise HTTPException(404, "Task not found")
    audit.log("task_update", task_id=task_id, details=str(updates))
    return m.TaskResponse(**task.to_dict())


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    tasks, _, audit, *_ = _get_state()
    if not tasks.delete(task_id):
        raise HTTPException(404, "Task not found")
    audit.log("task_delete", task_id=task_id)
    return {"deleted": True}


@router.post("/tasks/{task_id}/dispatch")
async def dispatch_task(task_id: str, body: m.DispatchRequest | None = None):
    """Classify and dispatch a task to an agent. Executes immediately for Ollama.

    Optional body allows overriding auto-classification:
    - agent: force dispatch to specific agent
    - bridge: force specific bridge
    - model: force specific Ollama model
    """
    tasks, dispatcher, audit, registry, ollama_bridge, claude_bridge, codex_bridge, gemini_bridge = _get_state()

    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    if task.status in ("running", "done"):
        raise HTTPException(400, f"Task already {task.status}")

    # Classify and route (with optional override)
    routing = dispatcher.dispatch(task)

    if body:
        if body.agent:
            routing["agent"] = body.agent
        if body.bridge:
            routing["bridge"] = body.bridge
        if body.model:
            routing["model"] = body.model

    bridge_name = routing["bridge"]

    # Assign agent
    tasks.assign(task_id, routing["agent"])
    registry.update_status(routing["agent"], "active", task_id)
    audit.log("dispatch", agent=routing["agent"], task_id=task_id, details=f"type={routing['task_type']}, bridge={bridge_name}")
    await broadcast("task_dispatch", {"task_id": task_id, "agent": routing["agent"], "task_type": routing["task_type"], "bridge": bridge_name})

    # Execute via appropriate bridge
    result = None
    if bridge_name == "ollama":
        tasks.update_status(task_id, "running")
        await broadcast("task_running", {"task_id": task_id, "agent": routing["agent"]})
        result = await ollama_bridge.execute(
            task,
            model=routing.get("model"),
            temperature=routing.get("temperature", 0.7),
            system_prompt=routing.get("system_prompt"),
        )
        if result.get("success"):
            tasks.complete(task_id, result["response"])
            registry.update_status(routing["agent"], "idle")
            audit.log("complete", agent=routing["agent"], task_id=task_id, status="done")
            await broadcast("task_complete", {"task_id": task_id, "agent": routing["agent"], "status": "done"})
        else:
            tasks.fail(task_id, result.get("error", "Unknown error"))
            registry.update_status(routing["agent"], "idle")
            audit.log("complete", agent=routing["agent"], task_id=task_id, status="failed", details=result.get("error", ""))
            await broadcast("task_failed", {"task_id": task_id, "agent": routing["agent"], "error": result.get("error", "")})

    elif bridge_name == "claude":
        result = await claude_bridge.execute(task)
        tasks.update_status(task_id, "running")
        audit.log("dispatched_file", agent="CLAUDE_LUSTRO", task_id=task_id, details=result.get("file", ""))
        await broadcast("task_running", {"task_id": task_id, "agent": "CLAUDE_LUSTRO", "mode": "async_file"})

    elif bridge_name == "codex":
        result = await codex_bridge.execute(task)
        tasks.update_status(task_id, "running")
        await broadcast("task_running", {"task_id": task_id, "agent": "CODEX", "mode": "async_file"})

    elif bridge_name == "gemini":
        result = await gemini_bridge.execute(task)
        tasks.update_status(task_id, "running")
        await broadcast("task_running", {"task_id": task_id, "agent": "GEMINI_ARCHITECT", "mode": "async_file"})

    else:
        raise HTTPException(400, f"Unknown bridge: {bridge_name}")

    return {
        "task_id": task_id,
        "routing": routing,
        "result": result,
        "task": tasks.get(task_id).to_dict(),
    }


@router.post("/tasks/{task_id}/poll")
async def poll_task(task_id: str):
    """Poll for async task result (Claude, Gemini, Codex).

    Checks if result file appeared in INBOX/ and auto-completes the task.
    """
    tasks, _, audit, registry, _, claude_bridge, codex_bridge, gemini_bridge = _get_state()

    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    if task.status == "done":
        return {"status": "done", "result": task.result, "task": task.to_dict()}

    if task.status != "running":
        return {"status": task.status, "message": f"Task is {task.status}, not running", "task": task.to_dict()}

    # Check bridge-specific result files
    result = None
    agent = task.assigned_to or ""

    if "CLAUDE" in agent:
        result = claude_bridge.check_result(task)
    elif "GEMINI" in agent:
        result = gemini_bridge.check_result(task)
    elif "CODEX" in agent:
        result = codex_bridge.check_result(task)

    if result and result.get("success"):
        tasks.complete(task_id, result["response"])
        registry.update_status(agent, "idle")
        audit.log("poll_complete", agent=agent, task_id=task_id, status="done")
        await broadcast("task_complete", {"task_id": task_id, "agent": agent, "status": "done"})

        # Archive files
        _archive_task_files(task_id, agent)

        return {"status": "done", "result": result["response"], "task": tasks.get(task_id).to_dict()}

    return {"status": "waiting", "message": "Result not yet available", "task": task.to_dict()}


def _archive_task_files(task_id: str, agent: str):
    """Move TASK and RESULT files to INBOX/DONE/."""
    from BUILDER.config import INBOX_DIR
    done_dir = INBOX_DIR / "DONE"
    done_dir.mkdir(parents=True, exist_ok=True)

    agent_short = agent.replace("_LUSTRO", "").replace("_ARCHITECT", "")
    patterns = [
        f"TASK_{task_id}_FOR_*.md",
        f"RESULT_{task_id}_FROM_*.md",
    ]

    import glob as glob_mod
    for pattern in patterns:
        for fpath in INBOX_DIR.glob(pattern):
            try:
                dest = done_dir / fpath.name
                fpath.rename(dest)
                logger.info(f"Archived {fpath.name} -> DONE/")
            except Exception as e:
                logger.warning(f"Failed to archive {fpath.name}: {e}")


@router.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry a failed task by re-dispatching it."""
    tasks, dispatcher, audit, registry, *_ = _get_state()

    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    if task.status not in ("failed", "done"):
        raise HTTPException(400, f"Can only retry failed/done tasks, current: {task.status}")

    # Reset task state
    task.status = "pending"
    task.result = None
    task.error = None
    task.assigned_to = None
    task.task_type = None
    task.touch()
    tasks._save()

    audit.log("task_retry", task_id=task_id, details="Reset to pending for re-dispatch")
    await broadcast("task_retry", {"task_id": task_id, "status": "pending"})

    # Re-dispatch
    return await dispatch_task(task_id)


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """Cancel a running or pending task."""
    tasks, _, audit, registry, *_ = _get_state()

    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    if task.status in ("done", "failed"):
        raise HTTPException(400, f"Task already {task.status}")

    agent = task.assigned_to
    tasks.fail(task_id, "Cancelled by user")
    if agent and registry:
        registry.update_status(agent, "idle")

    audit.log("task_cancel", task_id=task_id, agent=agent or "none")
    await broadcast("task_cancelled", {"task_id": task_id, "agent": agent})

    return {"cancelled": True, "task": tasks.get(task_id).to_dict()}
