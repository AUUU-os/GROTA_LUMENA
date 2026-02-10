"""
System endpoints — health, status, logs.
"""

import time
import logging
from fastapi import APIRouter

from BUILDER.config import VERSION

logger = logging.getLogger("builder.api.system")
router = APIRouter(tags=["system"])


def _get_state():
    from BUILDER.api.app import registry, tasks, audit, ollama_bridge, start_time
    return registry, tasks, audit, ollama_bridge, start_time


@router.get("/status")
async def get_status():
    registry, tasks, audit, _, start_time = _get_state()
    agents = registry.get_all()
    task_stats = tasks.stats()

    return {
        "status": "online",
        "version": VERSION,
        "uptime_seconds": round(time.time() - start_time, 1),
        "tasks": task_stats,
        "agents": {
            "total": len(agents),
            "by_status": _count_by(agents.values(), "status"),
        },
    }


@router.get("/health")
async def health_check():
    registry, tasks, _, ollama_bridge, start_time = _get_state()

    ollama_ok = await ollama_bridge.health()
    ollama_models = await ollama_bridge.list_models() if ollama_ok else []
    agents = registry.get_all()
    task_stats = tasks.stats()

    return {
        "builder": "online",
        "version": VERSION,
        "ollama": "online" if ollama_ok else "offline",
        "ollama_models": ollama_models,
        "agents_total": len(agents),
        "agents_active": sum(1 for a in agents.values() if a.status != "offline"),
        "tasks_pending": task_stats.get("pending", 0),
        "tasks_running": task_stats.get("running", 0),
        "uptime_seconds": round(time.time() - start_time, 1),
    }


@router.get("/logs")
async def get_logs(limit: int = 50):
    _, _, audit, _, _ = _get_state()
    lines = audit.read_recent(limit=limit)
    return {"logs": lines, "count": len(lines)}


@router.get("/routing")
async def get_routing():
    """Show current routing table."""
    from BUILDER.core.dispatcher import Dispatcher
    d = Dispatcher()
    return {"routing_table": d.get_routing_table()}


def _count_by(items, attr):
    counts = {}
    for item in items:
        val = getattr(item, attr, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


@router.get("/queue")
async def get_queue():
    """Returns the pending task queue sorted by priority with dependency status."""
    from BUILDER.api.app import tasks
    if not tasks:
        return {"queue": []}
    pending = tasks.list(status="pending")
    queue = []
    for t in pending:
        ready = tasks.is_ready(t.id) if hasattr(tasks, 'is_ready') else True
        queue.append({**t.to_dict(), "ready": ready})
    # Sort by priority
    prio = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    queue.sort(key=lambda x: (prio.get(x["priority"], 9), x["created_at"]))
    return {"queue": queue, "total": len(queue)}
