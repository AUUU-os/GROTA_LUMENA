from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import time
from corex.api.models import ExecuteRequest, ExecuteResponse
from corex.metrics import metrics_engine
from corex.api import state
from corex.input_validation import validate_daemon_command
from corex.memory_engine import memory_engine

router = APIRouter()


@router.post("/execute", response_model=ExecuteResponse)
async def execute_command(request: ExecuteRequest):
    if not state.daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")

    # Validate command input
    is_valid, sanitized_cmd, error = validate_daemon_command(request.command)
    if not is_valid:
        raise HTTPException(status_code=400, detail=f"Validation error: {error}")

    start_time = time.time()
    result = await state.daemon.execute_command(sanitized_cmd)
    latency = (time.time() - start_time) * 1000

    # Store execution in memory (best effort)
    try:
        await memory_engine.store_memory(
            content=f"Command: {sanitized_cmd} | Success: {result.get('success')}",
            memory_type="command",
            importance=5,
            metadata={"intent": result.get("intent"), "tags": ["command", "core"]},
            agent_id="core",
        )
    except Exception:
        pass

    metrics_engine.log_command(latency, result["success"])
    return ExecuteResponse(**result)
