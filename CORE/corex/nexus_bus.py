# NEXUS BUS - The Central Nervous System
# Protocol: Redis Streams
# Agents: GPT-4, Gemini, Dolphin (Local), Drive

import redis.asyncio as redis
import json
import logging
import asyncio
from typing import Dict, Any, Callable

logger = logging.getLogger("NEXUS")

class NexusBus:
    def __init__(self, redis_url="redis://localhost:6379"):
        self.redis_url = redis_url
        self.client = None
        self.stream_key = "lumen:nexus:stream"
        self.consumer_group = "lumen_agents"

    async def connect(self):
        self.client = redis.from_url(self.redis_url, decode_responses=True)
        try:
            await self.client.xgroup_create(self.stream_key, self.consumer_group, mkstream=True)
        except redis.ResponseError as e:
            # Group already exists
            pass
        logger.info("🔌 NEXUS BUS CONNECTED")

    async def publish(self, agent_id: str, message: Dict[str, Any], priority: str = "normal"):
        """Publish a message to the hive mind."""
        packet = {
            "agent": agent_id,
            "payload": json.dumps(message),
            "priority": priority,
            "ts": time.time()
        }
        await self.client.xadd(self.stream_key, packet)
        logger.debug(f"📤 Sent from {agent_id}")

    async def listen(self, agent_id: str, callback: Callable):
        """Listen for messages intended for this agent (or broadcast)."""
        consumer_name = f"consumer_{agent_id}"
        while True:
            try:
                # Read new messages
                streams = await self.client.xreadgroup(
                    self.consumer_group, consumer_name, {self.stream_key: ">"}, count=1, block=5000
                )
                
                for stream, messages in streams:
                    for message_id, data in messages:
                        # Process logic
                        sender = data.get("agent")
                        payload = json.loads(data.get("payload"))
                        
                        # Avoid echo
                        if sender != agent_id:
                            await callback(sender, payload)
                        
                        # Acknowledge
                        await self.client.xack(self.stream_key, self.consumer_group, message_id)
                        
            except Exception as e:
                logger.error(f"Bus Error: {e}")
                await asyncio.sleep(1)

nexus_bus = NexusBus()
