import asyncio
import logging
from typing import Callable, List, Dict
from collections import defaultdict

logger = logging.getLogger("EVENT_BUS")

class EventBus:
    """
    SYSTEM UPGRADE: Pub/Sub Event Architecture.
    Decouples modules from direct socket calls.
    """
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.history = []

    def subscribe(self, event_type: str, callback: Callable):
        self.subscribers[event_type].append(callback)
        logger.debug(f"🔌 Subscribed to {event_type}")

    async def publish(self, event_type: str, payload: dict):
        """Asynchronous event dispatch"""
        # 1. Log to history
        self.history.append({"type": event_type, "payload": payload})
        if len(self.history) > 1000: self.history.pop(0)

        # 2. Notify subscribers
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        asyncio.create_task(callback(payload))
                    else:
                        callback(payload)
                except Exception as e:
                    logger.error(f"❌ Event Callback Error ({event_type}): {e}")

        # 3. Global Broadcast (for UI)
        from corex.socket_manager import socket_manager
        await socket_manager.broadcast({"type": event_type, **payload})

# Singleton
event_bus = EventBus()
