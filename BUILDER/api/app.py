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
    """Handle new file in INBOX/."""
    logger.info(f"INBOX file detected: {path.name}")
    if audit:
        audit.log("inbox_file", details=str(path.name))


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
        allow_origins=["http://localhost:3001", "http://localhost:3000", "http://127.0.0.1:3001"],
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
