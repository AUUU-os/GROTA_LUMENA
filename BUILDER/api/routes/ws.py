"""
WebSocket live feed for real-time updates.
"""

import json
import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger("builder.api.ws")
router = APIRouter()

# Connected clients
_clients: list[WebSocket] = []


async def broadcast(event_type: str, data: dict):
    """Broadcast an event to all connected WebSocket clients."""
    event = {
        "type": event_type,
        "timestamp": datetime.now().isoformat(),
        "data": data,
    }
    message = json.dumps(event)
    disconnected = []
    for ws in _clients:
        try:
            await ws.send_text(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        _clients.remove(ws)


@router.websocket("/ws/feed")
async def ws_feed(websocket: WebSocket):
    await websocket.accept()
    _clients.append(websocket)
    logger.info(f"WebSocket client connected. Total: {len(_clients)}")

    try:
        # Send initial state
        from BUILDER.api.app import registry, tasks
        if registry and tasks:
            agents = registry.get_all()
            await websocket.send_text(json.dumps({
                "type": "init",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "agents": [a.to_dict() for a in agents.values()],
                    "tasks": [t.to_dict() for t in tasks.list()],
                },
            }))

        # Keep alive — wait for messages or disconnect
        while True:
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30)
                # Client can send ping
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong", "timestamp": datetime.now().isoformat()}))
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({"type": "heartbeat", "timestamp": datetime.now().isoformat()}))
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")
    finally:
        if websocket in _clients:
            _clients.remove(websocket)
        logger.info(f"WebSocket client disconnected. Total: {len(_clients)}")
