import asyncio
import logging
from datetime import datetime
from typing import List, Callable, Any

logger = logging.getLogger(__name__)

class OmegaWorker:
    """
    🐺 OMEGA BACKGROUND WORKER
    Handles long-running evolutionary tasks without blocking the main core.
    """
    def __init__(self):
        self.queue = asyncio.Queue()
        self.is_running = False
        self.processed_count = 0

    async def add_task(self, task_func: Callable, *args, **kwargs):
        """Adds a task to the background wataha."""
        await self.queue.put((task_func, args, kwargs))
        logger.info(f"📥 Task added to Omega Queue. Size: {self.queue.qsize()}")

    async def start(self):
        """Starts the background processing loop."""
        self.is_running = True
        logger.info("🚀 OMEGA WORKER: Starting background processing...")
        while self.is_running:
            task_func, args, kwargs = await self.queue.get()
            try:
                logger.info(f"⚙️ Executing background task: {task_func.__name__}")
                await task_func(*args, **kwargs)
                self.processed_count += 1
            except Exception as e:
                logger.error(f"❌ Background task failed: {e}")
            finally:
                self.queue.task_done()

    async def stop(self):
        self.is_running = False
        logger.info("🛑 OMEGA WORKER: Stopping...")

# Singleton
omega_worker = OmegaWorker()
