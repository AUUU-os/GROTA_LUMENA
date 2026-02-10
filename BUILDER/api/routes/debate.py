"""
Debate API routes — multi-agent debate endpoints.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from BUILDER.core.debate_engine import DebateEngine, SZTAB_AGENTS, DEFAULT_TOPICS

logger = logging.getLogger("builder.api.debate")

router = APIRouter(prefix="/debate", tags=["debate"])

# Singleton engine
_engine = DebateEngine()


class DebateStartRequest(BaseModel):
    topics: Optional[list[str]] = None
    agents: Optional[list[str]] = None  # subset of SZTAB_AGENTS keys


async def _run_debate_background(
    session_id: str,
    topics: list[str] | None,
    agents: dict | None,
):
    """Run debate in background task."""
    try:
        await _engine.run_debate(topics=topics, agents=agents)
    except Exception as e:
        logger.error(f"Background debate {session_id} failed: {e}")
        session = _engine.get_session(session_id)
        if session:
            session.status = "failed"
            session.error = str(e)


@router.post("/start")
async def start_debate(
    request: DebateStartRequest,
    bg: BackgroundTasks,
):
    """Start a new multi-agent debate session."""
    topics = request.topics or DEFAULT_TOPICS

    # Filter agents if subset requested
    agents = None
    if request.agents:
        agents = {
            k: v for k, v in SZTAB_AGENTS.items()
            if k in request.agents
        }
        if not agents:
            raise HTTPException(
                status_code=400,
                detail=f"No valid agents found. Available: {list(SZTAB_AGENTS.keys())}",
            )

    # Create session first to get ID
    from BUILDER.core.debate_engine import DebateSession
    from datetime import datetime
    session = DebateSession(
        topics=topics,
        status="running",
        started_at=datetime.utcnow().isoformat(),
    )
    _engine._sessions[session.id] = session

    # Run in background
    bg.add_task(_run_debate_background, session.id, topics, agents)

    return {
        "session_id": session.id,
        "status": "running",
        "topics": len(topics),
        "agents": len(agents) if agents else len(SZTAB_AGENTS),
        "message": "Debate started in background. Poll /debate/{id} for status.",
    }


@router.get("/{session_id}")
async def get_debate_status(session_id: str):
    """Get debate session status and partial results."""
    session = _engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Debate session not found")

    result = session.to_dict()
    # Add partial results summary
    if session.results:
        result["completed_topics_detail"] = [
            {
                "topic": r.topic[:80],
                "analyses": len(r.analyses),
                "rebuttals": len(r.rebuttals),
                "votes": len(r.votes),
                "action_items": len(r.action_items),
            }
            for r in session.results
        ]

    return result


@router.get("/{session_id}/report")
async def get_debate_report(session_id: str):
    """Get the full Markdown report for a completed debate."""
    session = _engine.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Debate session not found")

    if session.status not in ("completed", "failed"):
        return {
            "status": session.status,
            "message": "Debate still in progress. Check back later.",
            "completed_topics": len(session.results),
            "total_topics": len(session.topics),
        }

    report = _engine.generate_report(session)
    return {
        "session_id": session_id,
        "status": session.status,
        "report": report,
    }


@router.get("/history", name="debate_history")
async def list_debates():
    """List all past and current debate sessions."""
    return {
        "sessions": _engine.list_sessions(),
        "available_agents": list(SZTAB_AGENTS.keys()),
        "default_topics": DEFAULT_TOPICS,
    }
