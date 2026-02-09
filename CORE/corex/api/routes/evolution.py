from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
from corex.evolution_engine import evolution_engine
from corex.evolution_hub import evolution_hub

router = APIRouter()

@router.get("/status")
async def get_evo_status():
    return {
        "is_active": True,
        "nodes": evolution_hub.list_swarm(),
        "history_count": len(evolution_engine.history)
    }

@router.get("/history")
async def get_history():
    return {"history": evolution_engine.history}

@router.post("/analyze")
async def analyze_file(file_path: str):
    return evolution_engine.analyze_module_depth(file_path)

@router.post("/rollback")
async def execute_rollback(backup_id: str = None):
    result = evolution_engine.rollback(backup_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

@router.get("/swarm")
async def list_swarm():
    return {"nodes": evolution_hub.list_swarm()}

@router.post("/sync")
async def sync_swarm():
    return evolution_hub.sync_nodes()
