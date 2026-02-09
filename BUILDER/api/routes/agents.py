"""
Agent registry endpoints.
"""

import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("builder.api.agents")
router = APIRouter(tags=["agents"])


def _get_state():
    from BUILDER.api.app import registry, audit, ollama_bridge
    return registry, audit, ollama_bridge


@router.get("/agents")
async def list_agents():
    registry, *_ = _get_state()
    agents = registry.get_all()
    return {
        "agents": [a.to_dict() for a in agents.values()],
        "total": len(agents),
    }


@router.get("/agents/{name}")
async def get_agent(name: str):
    registry, *_ = _get_state()
    agent = registry.get_agent(name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")
    data = agent.to_dict()
    data["who_am_i"] = agent.who_am_i_raw
    return data


@router.post("/agents/{name}/ping")
async def ping_agent(name: str):
    """Check if an agent is reachable."""
    registry, audit, ollama_bridge = _get_state()
    agent = registry.get_agent(name)
    if not agent:
        raise HTTPException(404, f"Agent '{name}' not found")

    alive = False
    if agent.bridge_type == "ollama":
        alive = await ollama_bridge.health()
    elif agent.bridge_type == "human":
        alive = True  # SHAD is always there
    else:
        # File-based agents — check if their STATE.log was updated recently
        from BUILDER.config import M_AI_SELF_DIR
        from datetime import datetime, timedelta
        state_file = M_AI_SELF_DIR / name / "STATE.log"
        if state_file.exists():
            import os
            mtime = datetime.fromtimestamp(os.path.getmtime(str(state_file)))
            alive = (datetime.now() - mtime) < timedelta(hours=24)

    status = "online" if alive else "offline"
    registry.update_status(name, "idle" if alive else "offline")
    audit.log("ping", agent=name, status=status)

    return {"agent": name, "alive": alive, "status": status}


@router.post("/agents/refresh")
async def refresh_agents():
    """Force re-scan of M-AI-SELF/ directory."""
    registry, audit, _ = _get_state()
    agents = registry.scan_agents()
    audit.log("agents_refresh", details=f"Found {len(agents)} agents")
    return {
        "agents": [a.to_dict() for a in agents.values()],
        "total": len(agents),
    }
