import time
import socketio
import logging
import asyncio

logger = logging.getLogger("SOCKET-MANAGER")

class SocketManager:
    """Manages high-speed WebRTC/WebSocket streams for Voice and Live Data."""
    def __init__(self):
        self.sio = socketio.AsyncServer(async_mode='asgi', cors_allowed_origins='*')
        self.app = socketio.ASGIApp(self.sio)
        self._register_handlers()

    def _register_handlers(self):
        @self.sio.on('connect')
        def connect(sid, environ):
            logger.info(f"✨ Heartbeat Link Established: {sid}")

        
        @self.sio.on('neural_sync')
        async def handle_neural_sync(sid, data):
            logger.info(f"? Neural Sync via Socket: {sid}")
            await self.sio.emit('sync_feedback', {'status': 'aligned', 'ts': time.time()})

        @self.sio.on('voice_stream')
        async def handle_voice(sid, data):
            """Processes incoming Opus/WebRTC chunks."""
            logger.info(f"🐺 Voice Stream Received from {sid}")

    async def broadcast_resonance(self, data: dict):
        """Sends real-time system metrics to the Dashboard."""
        await self.sio.emit('pulse', data)

socket_manager = SocketManager()
