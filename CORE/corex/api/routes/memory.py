from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from corex.api.models import (
    MemoryStoreRequest,
    MemoryStoreResponse,
    MemorySearchRequest,
    MemorySearchResponse,
)
from corex.memory_engine import memory_engine

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


@router.get("/memory/stats")
async def memory_stats():
    return {"success": True, "stats": memory_engine.vector_db.get_stats()}


@router.get("/memory/export")
async def memory_export(limit: int = 1000, offset: int = 0, agent_id: str = None, session_id: str = None):
    results = await memory_engine.retrieve_memories(
        query="",
        limit=limit,
        strategy="temporal",
        offset=offset,
        agent_id=agent_id,
        session_id=session_id,
    )
    return {"success": True, "results": results}
