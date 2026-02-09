"""
LUMEN CORE API SERVER v19.0.0
Refactored for high-performance, asynchronous database integration and resonance scaling.
Adheres to PEP 8 and robust engineering standards.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

import uvicorn
from fastapi import FastAPI, Depends, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel
from sqlmodel.ext.asyncio.session import AsyncSession
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

# --- LUMEN MODULES ---
from corex.database.session import init_db, get_session
from corex.database.models import TimelineEvent
from corex.logger import setup_lumen_logger
from corex.auth import verify_token
from corex.execute import execute_system_command
from corex.resonance_physics import resonance_engine
from corex.ollama_bridge import ollama_bridge
from corex.swarm.router import router as swarm_router
from corex.omega import omega_shield, OmegaCommand
from corex.monitor import resource_monitor
from corex.health import health_checker
from corex.memory_engine import memory_engine

# --- INITIALIZATION ---
logger = setup_lumen_logger(
    path="./logs", level="INFO", output_file="api.log", max_size_mb=100
)

# Global Cache for Memoization (Agent/Session metadata)
_RESONANCE_CACHE: Dict[str, Any] = {}


class ChronicleManager:
    """Manages idempotent logging to the central database."""

    @staticmethod
    async def log_event(event_type: str, agent_id: str, content: dict, session_id: str):
        """Asynchronously persists events to the Timeline."""
        async for db in get_session():
            try:
                event = TimelineEvent(
                    session_id=session_id,
                    agent_id=agent_id,
                    event_type=event_type,
                    content=content,
                    timestamp=datetime.utcnow(),
                )
                db.add(event)
                await db.commit()
            except Exception as e:
                logger.error(f"Chronicle Failure: {e}")
            finally:
                await db.close()
            break


class SecurityMiddleware(BaseHTTPMiddleware):
    """Robust rate limiting and security inspection."""

    def __init__(self, app):
        super().__init__(app)
        self.request_log = {}

    RATE_LIMIT_EXEMPT = {"/api/v1/health", "/docs", "/openapi.json"}

    async def dispatch(self, request: Request, call_next):
        # 1. IP Rate Limiting (skip health/docs endpoints)
        client_ip = request.client.host
        now = time.time()
        if request.url.path not in self.RATE_LIMIT_EXEMPT:
            if (
                client_ip in self.request_log
                and now - self.request_log[client_ip] < 0.01
            ):
                return ORJSONResponse({"error": "Rate limit exceeded"}, status_code=429)
        self.request_log[client_ip] = now

        # 2. Security Shield (Omega)
        if request.method == "POST" and "/api/" in request.url.path:
            try:
                body = await request.json()
                cmd = body.get("command", "")
                if cmd:
                    is_safe, reason = await omega_shield.inspect_command(
                        OmegaCommand(command=cmd)
                    )
                    if not is_safe:
                        logger.warning(f"🚨 Security Block: {reason}")
                        return ORJSONResponse(
                            {"error": f"Security Violation: {reason}"}, status_code=403
                        )
            except Exception:
                pass

        response = await call_next(request)
        return response


# --- API APP DEFINITION ---
app = FastAPI(
    title="LUMEN CORE", version="19.0.0", default_response_class=ORJSONResponse
)

# Middleware Chain
app.add_middleware(SecurityMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8001"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(swarm_router, prefix="/api/v1/swarm")


# --- DATA MODELS ---
class CommandRequest(BaseModel):
    command: str
    mode: str = "design"
    session_id: Optional[str] = None


class MemoryStoreRequest(BaseModel):
    content: str
    memory_type: str = "general"
    importance: int = 5
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: Optional[str] = None
    limit: int = 5
    strategy: str = "hybrid"
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    offset: int = 0


# --- LIFECYCLE ---
@app.on_event("startup")
async def startup_event():
    logger.info("LUMEN CORE v19.0 AWAKENING...")
    await init_db()

    # Warm up Resonance Engine
    resonance_engine.calculate_current_resonance(963.0)

    logger.info("System Operational. Chronicle is active.")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("LUMEN CORE shutting down gracefully...")
    # Allow pending tasks to complete
    await asyncio.sleep(0.5)
    logger.info("Shutdown complete.")


# --- ENDPOINTS ---


@app.get("/api/v1/health")
async def health_check():
    """Idempotent health pulse."""
    return {
        "status": "OPERATIONAL",
        "resonance": resonance_engine.get_sync_score(),
        "pulse": resource_monitor.get_pulse(),
    }


@app.post("/api/v1/execute")
async def execute(
    request: CommandRequest,
    bg: BackgroundTasks,
    db: AsyncSession = Depends(get_session),
    token: str = Depends(verify_token),
):
    """
    Core execution endpoint with Chronicle persistence.
    Metric: Target latency < 50ms (achieved via BackgroundTasks).
    """
    # 1. Session Management
    session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"

    # 2. Log Interaction (Async)
    bg.add_task(
        ChronicleManager.log_event,
        "message",
        "shad",
        {"command": request.command, "mode": request.mode},
        session_id,
    )

    # 3. Execution Path
    if request.mode == "exec":
        result = execute_system_command(request.command)
        bg.add_task(
            ChronicleManager.log_event,
            "tool_use",
            "system",
            {"result": "executed", "command": request.command},
            session_id,
        )
        # Best-effort memory store
        try:
            await memory_engine.store_memory(
                content=f"Command: {request.command} | Exec: True",
                memory_type="command",
                importance=5,
                metadata={"mode": "exec"},
                session_id=session_id,
                agent_id="system",
            )
        except Exception:
            pass
        return {"action": "exec", "result": result, "sid": session_id}

    # Best-effort memory store for non-exec
    try:
        await memory_engine.store_memory(
            content=f"Command: {request.command} | Exec: False",
            memory_type="command",
            importance=4,
            metadata={"mode": request.mode},
            session_id=session_id,
            agent_id="shad",
        )
    except Exception:
        pass

    return {"action": "ack", "sid": session_id}


@app.post("/api/v1/chat/local")
async def local_chat(request: Dict[str, Any], bg: BackgroundTasks):
    """Optimized local inference via Ollama Bridge."""
    prompt = request.get("prompt")
    model = request.get("model", "dolphin-llama3")

    # Fast Generate (with caching inside bridge)
    response = await ollama_bridge.generate(
        prompt=prompt, model=model, format="json" if "json" in prompt.lower() else None
    )

    return response


@app.get("/api/v1/health/deep")
async def deep_health_check():
    """Comprehensive health check: Ollama, disk, memory, CPU."""
    return await health_checker.deep_check()


@app.get("/api/v1/stream")
async def sse_stream(request: Request):
    """Server-Sent Events endpoint for live dashboard updates."""

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            pulse = resource_monitor.get_pulse()
            data = json.dumps({"type": "pulse", "data": pulse})
            yield f"data: {data}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/v1/agent/run")
async def agent_run(request: Dict[str, Any], bg: BackgroundTasks):
    """Execute a task through the Agent Loop with multi-step reasoning."""
    from corex.agent_loop import create_agent_loop

    task = request.get("task", "")
    max_steps = request.get("max_steps", 10)
    model = request.get("model")

    if not task:
        return ORJSONResponse({"error": "task is required"}, status_code=400)

    loop = create_agent_loop(max_steps=max_steps, model=model)
    result = await loop.run(task)

    return result


@app.post("/api/v1/memory/store")
async def memory_store(request: MemoryStoreRequest):
    entry = await memory_engine.store_memory(
        content=request.content,
        memory_type=request.memory_type,
        importance=request.importance,
        metadata=request.metadata or {},
        session_id=request.session_id,
        agent_id=request.agent_id,
    )
    return {"success": True, "entry_id": entry.id, "embedding_id": entry.embedding_id}


@app.post("/api/v1/memory/search")
async def memory_search(request: MemorySearchRequest):
    results = await memory_engine.retrieve_memories(
        query=request.query or "",
        limit=request.limit,
        strategy=request.strategy,
        agent_id=request.agent_id,
        session_id=request.session_id,
        offset=request.offset,
    )
    return {"success": True, "results": results}


@app.get("/api/v1/memory/recent")
async def memory_recent(limit: int = 10, offset: int = 0, agent_id: str = None, session_id: str = None):
    results = await memory_engine.retrieve_memories(
        query="",
        limit=limit,
        strategy="temporal",
        offset=offset,
        agent_id=agent_id,
        session_id=session_id,
    )
    return {"success": True, "results": results}


@app.get("/api/v1/memory/stats")
async def memory_stats():
    return {"success": True, "stats": memory_engine.vector_db.get_stats()}


@app.get("/api/v1/memory/export")
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
