from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from corex.api.models import (
    MemoryStoreRequest,
    MemoryStoreResponse,
    MemorySearchRequest,
    MemorySearchResponse,
)
from corex.memory_engine import memory_engine
import csv
import io
from fastapi.responses import StreamingResponse

router = APIRouter()


@router.post("/memory/store", response_model=MemoryStoreResponse)
async def store_memory(request: MemoryStoreRequest):
    if not request.content:
        raise HTTPException(status_code=400, detail="content is required")

    entry = await memory_engine.store_memory(
        content=request.content,
        memory_type=request.memory_type or "general",
        importance=request.importance or 5,
        metadata=request.metadata or {},
        session_id=request.session_id,
        agent_id=request.agent_id,
    )
    return MemoryStoreResponse(
        success=True, entry_id=entry.id, embedding_id=entry.embedding_id
    )


@router.post("/memory/search", response_model=MemorySearchResponse)
async def search_memory(request: MemorySearchRequest):
    query = request.query or ""
    results = await memory_engine.retrieve_memories(
        query=query,
        limit=request.limit or 5,
        strategy=request.strategy or "hybrid",
        agent_id=request.agent_id,
        session_id=request.session_id,
        offset=request.offset or 0,
    )
    return MemorySearchResponse(success=True, results=results)


@router.get("/memory/recent")
async def recent_memory(limit: int = 10, offset: int = 0, agent_id: str = None, session_id: str = None):
    results = await memory_engine.retrieve_memories(
        query="",
        limit=limit,
        strategy="temporal",
        offset=offset,
        agent_id=agent_id,
        session_id=session_id,
    )
    return {"success": True, "results": results}


@router.get("/memory/collective")
async def collective_memory(limit: int = 10, offset: int = 0):
    results = await memory_engine.retrieve_memories(
        query="",
        limit=limit,
        strategy="temporal",
        offset=offset,
        agent_id="collective",
    )
    return {"success": True, "results": results}


@router.get("/memory/stats")
async def memory_stats():
    return {"success": True, "stats": memory_engine.vector_db.get_stats()}


@router.get("/memory/metrics")
async def memory_metrics():
    results = await memory_engine.retrieve_memories(query="", limit=1000, strategy="temporal")
    by_agent = {}
    by_type = {}
    by_tag = {}
    for r in results:
        agent = r.get("agent_id") or "unknown"
        mtype = r.get("memory_type") or "unknown"
        by_agent[agent] = by_agent.get(agent, 0) + 1
        by_type[mtype] = by_type.get(mtype, 0) + 1
        meta = r.get("meta_data") or {}
        tags = meta.get("tags") or []
        if isinstance(tags, list):
            for t in tags:
                by_tag[t] = by_tag.get(t, 0) + 1
    return {"success": True, "by_agent": by_agent, "by_type": by_type, "by_tag": by_tag}


@router.get("/memory/export")
async def memory_export(limit: int = 1000, offset: int = 0, agent_id: str = None, session_id: str = None, tag: str = None):
    results = await memory_engine.retrieve_memories(
        query="",
        limit=limit,
        strategy="temporal",
        offset=offset,
        agent_id=agent_id,
        session_id=session_id,
    )
    if tag:
        results = [
            r for r in results
            if isinstance(r.get("meta_data"), dict)
            and isinstance(r["meta_data"].get("tags"), list)
            and tag in r["meta_data"]["tags"]
        ]
    return {"success": True, "results": results}


@router.get("/memory/export.csv")
async def memory_export_csv(limit: int = 1000, offset: int = 0, agent_id: str = None, session_id: str = None, tag: str = None):
    results = await memory_engine.retrieve_memories(
        query="",
        limit=limit,
        strategy="temporal",
        offset=offset,
        agent_id=agent_id,
        session_id=session_id,
    )
    if tag:
        results = [
            r for r in results
            if isinstance(r.get("meta_data"), dict)
            and isinstance(r["meta_data"].get("tags"), list)
            and tag in r["meta_data"]["tags"]
        ]
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["id", "created_at", "agent_id", "session_id", "memory_type", "content", "importance", "tags"])
    for r in results:
        meta = r.get("meta_data") or {}
        tags = meta.get("tags", [])
        writer.writerow([
            r.get("id"),
            r.get("created_at"),
            r.get("agent_id"),
            r.get("session_id"),
            r.get("memory_type"),
            r.get("content"),
            r.get("importance"),
            ",".join(tags) if isinstance(tags, list) else ""
        ])
    buffer.seek(0)
    return StreamingResponse(iter([buffer.getvalue()]), media_type="text/csv")


@router.post("/memory/backup/run")
async def memory_backup_run(keep_days: int = 7):
    path = await memory_engine.backup_to_file(keep_days=keep_days)
    return {"success": True, "path": path}


@router.post("/memory/backup/cleanup")
async def memory_backup_cleanup(keep_days: int = 7):
    removed = memory_engine.cleanup_backups(keep_days=keep_days)
    return {"success": True, "removed": removed}
