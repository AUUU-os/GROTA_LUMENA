from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import logging
import json

logger = logging.getLogger("MOBILE_API")
router = APIRouter()

class MobileConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("📱 Mobile Device Connected.")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("📱 Mobile Device Disconnected.")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

mobile_manager = MobileConnectionManager()

@router.websocket("/ws/mobile")
async def mobile_websocket_endpoint(websocket: WebSocket):
    await mobile_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Handle mobile-specific commands here
            logger.info(f"📱 Received from mobile: {data}")
    except WebSocketDisconnect:
        mobile_manager.disconnect(websocket)
