"""
Task CRUD + dispatch endpoints.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException

from BUILDER.api import models as m

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
async def dispatch_task(task_id: str):
    """Classify and dispatch a task to an agent. Executes immediately for Ollama."""
    tasks, dispatcher, audit, registry, ollama_bridge, claude_bridge, codex_bridge, gemini_bridge = _get_state()

    task = tasks.get(task_id)
    if not task:
        raise HTTPException(404, "Task not found")

    if task.status in ("running", "done"):
        raise HTTPException(400, f"Task already {task.status}")

    # Classify and route
    routing = dispatcher.dispatch(task)
    bridge_name = routing["bridge"]

    # Assign agent
    tasks.assign(task_id, routing["agent"])
    registry.update_status(routing["agent"], "active", task_id)
    audit.log("dispatch", agent=routing["agent"], task_id=task_id, details=f"type={routing['task_type']}, bridge={bridge_name}")

    # Execute via appropriate bridge
    result = None
    if bridge_name == "ollama":
        tasks.update_status(task_id, "running")
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
        else:
            tasks.fail(task_id, result.get("error", "Unknown error"))
            registry.update_status(routing["agent"], "idle")
            audit.log("complete", agent=routing["agent"], task_id=task_id, status="failed", details=result.get("error", ""))

    elif bridge_name == "claude":
        result = await claude_bridge.execute(task)
        tasks.update_status(task_id, "running")
        audit.log("dispatched_file", agent="CLAUDE_LUSTRO", task_id=task_id, details=result.get("file", ""))

    elif bridge_name == "codex":
        result = await codex_bridge.execute(task)
        tasks.update_status(task_id, "running")

    elif bridge_name == "gemini":
        result = await gemini_bridge.execute(task)
        tasks.update_status(task_id, "running")

    else:
        raise HTTPException(400, f"Unknown bridge: {bridge_name}")

    return {
        "task_id": task_id,
        "routing": routing,
        "result": result,
        "task": tasks.get(task_id).to_dict(),
    }
