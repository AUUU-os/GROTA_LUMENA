from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from corex.api import state

router = APIRouter()

@router.get("")
async def list_modules():
    if not state.daemon: raise HTTPException(status_code=503, detail="Daemon not initialized")
    return {"modules": state.daemon.router.get_status()}

@router.post("/{module_name}/{operation}")
async def execute_module_operation(module_name: str, operation: str, params: Dict[str, Any]):
    if not state.daemon: raise HTTPException(status_code=503, detail="Daemon not initialized")
    
    module = state.daemon.router.modules.get(module_name)
    if not module: raise HTTPException(status_code=404, detail=f"Module {module_name} not found")
    
    try:
        return await module.execute(operation, params)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
