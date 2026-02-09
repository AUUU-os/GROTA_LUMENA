"""
FastAPI application for Builder daemon.
"""
from __future__ import annotations

import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from BUILDER.config import VERSION, PORT
from BUILDER.core.agent_registry import AgentRegistry
from BUILDER.core.task_manager import TaskManager
from BUILDER.core.dispatcher import Dispatcher
from BUILDER.core.audit import AuditLog
from BUILDER.core.file_watcher import FileWatcher
from BUILDER.bridges.ollama import OllamaBridge
from BUILDER.bridges.claude import ClaudeBridge
from BUILDER.bridges.codex import CodexBridge
from BUILDER.bridges.gemini import GeminiBridge

logger = logging.getLogger("builder.api")

# Global state — initialized at startup
registry: AgentRegistry | None = None
tasks: TaskManager | None = None
dispatcher: Dispatcher | None = None
audit: AuditLog | None = None
watcher: FileWatcher | None = None
ollama_bridge: OllamaBridge | None = None
claude_bridge: ClaudeBridge | None = None
codex_bridge: CodexBridge | None = None
gemini_bridge: GeminiBridge | None = None
start_time: float = 0


def _on_inbox_file(path):
    """Handle new file in INBOX/. Auto-pickup RESULT files to complete tasks."""
    import re
    from pathlib import Path
    path = Path(path) if not isinstance(path, Path) else path
    name = path.name
    logger.info(f"INBOX file detected: {name}")

    if audit:
        audit.log("inbox_file", details=name)

    # Auto-pickup: RESULT_{task_id}_FROM_{agent}.md
    match = re.match(r"RESULT_([a-f0-9]+)_FROM_(\w+)\.md", name)
    if match and tasks:
        task_id = match.group(1)
        agent_name = match.group(2).upper()
        task = tasks.get(task_id)
        if task and task.status == "running":
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                tasks.complete(task_id, content)
                if registry:
                    registry.update_status(task.assigned_to or agent_name, "idle")
                if audit:
                    audit.log("auto_complete", agent=agent_name, task_id=task_id, status="done", details="Picked up from INBOX")
                logger.info(f"Auto-completed task {task_id} from {agent_name}")

                # Archive files to INBOX/DONE/
                _archive_files(task_id)

                # Broadcast via WebSocket
                _schedule_broadcast("task_complete", {
                    "task_id": task_id,
                    "agent": agent_name,
                    "status": "done",
                })
            except Exception as e:
                logger.error(f"Failed to auto-pickup result for {task_id}: {e}")

    # Also detect CODEX_RESULT_*.md
    codex_match = re.match(r"CODEX_RESULT_(\d{8}_\d{6})\.md", name)
    if codex_match and tasks:
        # Find running task assigned to CODEX
        for t in tasks.list(status="running"):
            if t.assigned_to == "CODEX":
                try:
                    content = path.read_text(encoding="utf-8", errors="replace")
                    tasks.complete(t.id, content)
                    if registry:
                        registry.update_status("CODEX", "idle")
                    if audit:
                        audit.log("auto_complete", agent="CODEX", task_id=t.id, status="done", details="Codex result picked up")
                    _archive_files(t.id)
                    _schedule_broadcast("task_complete", {"task_id": t.id, "agent": "CODEX", "status": "done"})
                except Exception as e:
                    logger.error(f"Failed to pickup Codex result: {e}")
                break


def _archive_files(task_id: str):
    """Move TASK and RESULT files for a completed task to INBOX/DONE/."""
    from BUILDER.config import INBOX_DIR
    done_dir = INBOX_DIR / "DONE"
    done_dir.mkdir(parents=True, exist_ok=True)

    for pattern in [f"TASK_{task_id}_FOR_*.md", f"RESULT_{task_id}_FROM_*.md"]:
        for fpath in INBOX_DIR.glob(pattern):
            try:
                dest = done_dir / fpath.name
                fpath.rename(dest)
                logger.info(f"Archived {fpath.name} -> DONE/")
            except Exception as e:
                logger.warning(f"Failed to archive {fpath.name}: {e}")


def _schedule_broadcast(event_type: str, data: dict):
    """Schedule a WebSocket broadcast from a sync context (FileWatcher thread)."""
    import asyncio
    from BUILDER.api.routes.ws import broadcast
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast(event_type, data))
        else:
            loop.run_until_complete(broadcast(event_type, data))
    except RuntimeError:
        pass  # No event loop available


def _on_state_change(path):
    """Handle STATE.log change in M-AI-SELF/."""
    agent_name = path.parent.name
    logger.info(f"State change: {agent_name}")
    if registry:
        registry.scan_agents()
    if audit:
        audit.log("state_change", agent=agent_name)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    global registry, tasks, dispatcher, audit, watcher, start_time
    global ollama_bridge, claude_bridge, codex_bridge, gemini_bridge

    start_time = time.time()

    # Initialize components
    registry = AgentRegistry()
    tasks = TaskManager()
    dispatcher = Dispatcher()
    audit = AuditLog()
    ollama_bridge = OllamaBridge()
    claude_bridge = ClaudeBridge()
    codex_bridge = CodexBridge()
    gemini_bridge = GeminiBridge()

    # Start file watcher
    watcher = FileWatcher(
        on_inbox_file=_on_inbox_file,
        on_state_change=_on_state_change,
    )
    try:
        watcher.start()
    except Exception as e:
        logger.warning(f"FileWatcher failed to start: {e}")

    audit.log("startup", details=f"Builder v{VERSION} started on port {PORT}")
    logger.info(f"Builder v{VERSION} started. Agents: {len(registry.get_all())}")

    yield

    # Shutdown
    if watcher:
        watcher.stop()
    if audit:
        audit.log("shutdown", details="Builder stopped")
    logger.info("Builder stopped")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Builder — GROTA LUMENA Orchestrator",
        version=VERSION,
        lifespan=lifespan,
    )

    # CORS for Dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3001", "http://127.0.0.1:3002"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routes
    from BUILDER.api.routes import tasks as tasks_routes
    from BUILDER.api.routes import agents as agents_routes
    from BUILDER.api.routes import system as system_routes
    from BUILDER.api.routes import ws as ws_routes

    app.include_router(tasks_routes.router, prefix="/api/v1")
    app.include_router(agents_routes.router, prefix="/api/v1")
    app.include_router(system_routes.router, prefix="/api/v1")
    app.include_router(ws_routes.router)

    return app
