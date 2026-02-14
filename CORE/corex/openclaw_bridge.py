\"\"\"
OpenClaw Bridge - LUMEN OMEGA
Connects the Python Backend with the Node.js OpenClaw Gateway.
\"\"\"

import aiohttp
import asyncio
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class OpenClawBridge:
    def __init__(self, gateway_url: str = \"ws://127.0.0.1:18789\"):
        self.gateway_url = gateway_url
        self.session = None
        self.ws = None

    async def connect(self):
        \"\"\"Establish connection to the OpenClaw Gateway.\"\"\"
        self.session = aiohttp.ClientSession()
        try:
            self.ws = await self.session.ws_connect(self.gateway_url)
            logger.info(f\"đźŚž Connected to OpenClaw Gateway at {self.gateway_url}\")
        except Exception as e:
            logger.error(f\"đźŚž Connection failed: {e}\")
            await self.session.close()

    async def send_message(self, to: str, message: str):
        \"\"\"Send a message through OpenClaw.\"\"\"
        if not self.ws:
            await self.connect()
        
        payload = {
            \"type\": \"message_send\",
            \"data\": {
                \"to\": to,
                \"message\": message
            }
        }
        await self.ws.send_json(payload)
        logger.info(f\"đźŚž Message sent to {to}\")

    async def listen_loop(self, callback):
        \"\"\"Listen for incoming messages from OpenClaw.\"\"\"
        if not self.ws:
            await self.connect()
        
        async for msg in self.ws:
            if msg.type == aiohttp.WSMsgType.TEXT:
                data = json.loads(msg.data)
                await callback(data)
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break

    async def close(self):
        if self.session:
            await self.session.close()

openclaw_bridge = OpenClawBridge()
\"\"\"
Integration Guide:
1. Start OpenClaw Gateway (pnpm gateway)
2. Use this bridge in api_server.py to route messages.
\"\"\"
