from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Dict, Any
from corex.api.models import StatusResponse
from corex.resonance_physics import resonance_engine

from corex.api import state

router = APIRouter()

@router.get("/status", response_model=StatusResponse)
async def get_status():
    if not state.daemon:
        raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    status = state.daemon.get_status()
    res_state = resonance_engine.calculate_current_resonance(963.0)
    status["stats"]["resonance"] = {
        "amplitude": res_state.amplitude,
        "energy": res_state.energy,
        "sync_score": resonance_engine.get_sync_score(),
        "frequency": 963.0
    }
    return StatusResponse(**status)

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "daemon_running": state.daemon.is_running if state.daemon else False,
        "db": "connected"
    }

@router.get("/interface")
async def read_interface():
    return FileResponse('static/index.html')
