from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from corex.voice_manager import voice_manager

router = APIRouter()

@router.post("/start")
async def start_voice():
    return voice_manager.start()

@router.post("/stop")
async def stop_voice():
    return voice_manager.stop()

@router.get("/status")
async def get_voice_status():
    return voice_manager.get_state()
