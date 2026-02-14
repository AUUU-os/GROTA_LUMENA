import socket
import json
import asyncio
import logging
from corex.socket_manager import socket_manager

logger = logging.getLogger("PULSE-RECEIVER")

class PulseReceiver:
    """Listens for UDP pulses from all distributed nodes (Pack)."""
    def __init__(self, port=9999):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("127.0.0.1", self.port))
        self.sock.setblocking(False)

    async def listen(self):
        logger.info(f"đź“Ą Pulse Receiver Active on port {self.port}")
        loop = asyncio.get_event_loop()
        while True:
            try:
                data, addr = await loop.run_in_executor(None, self.sock.recvfrom, 1024)
                pulse = json.loads(data.decode())
                logger.info(f"đź’Ş Received Pulse from {pulse['node']}: {pulse['archetype']}")
                
                # Forward to Dashboard via WebSocket
                await socket_manager.broadcast_resonance(pulse)
            except Exception:
                await asyncio.sleep(0.1)

pulse_receiver = PulseReceiver()
