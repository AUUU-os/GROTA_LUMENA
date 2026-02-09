"""
LUMEN ASYNC WORKER
Handles long-running tasks autonomously.
"""

import asyncio
import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Callable

logger = logging.getLogger(__name__)

class AsyncWorker:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.is_running = False

    async def start(self):
        """Standard start method for system synchronization."""
        self.is_running = True
        logger.info("🚀 ASYNC WORKER: Standing by for tasks...")
        # (This worker uses asyncio.create_task per call, 
        # but we keep the method for lifecycle consistency)
        while self.is_running:
            await asyncio.sleep(1)

    async def run_task(self, name: str, coro: Callable, *args, **kwargs):
        """Enqueues a task and returns a tracking ID."""
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {
            "name": name,
            "status": "pending",
            "start_time": datetime.now().isoformat(),
            "result": None
        }
        
        # Run in background
        asyncio.create_task(self._executor(task_id, coro, *args, **kwargs))
        return task_id

    async def _executor(self, task_id: str, coro: Callable, *args, **kwargs):
        self.tasks[task_id]["status"] = "running"
        try:
            result = await coro(*args, **kwargs)
            self.tasks[task_id]["status"] = "completed"
            self.tasks[task_id]["result"] = result
        except Exception as e:
            self.tasks[task_id]["status"] = "failed"
            self.tasks[task_id]["error"] = str(e)
            logger.error(f"Task {task_id} failed: {e}")

    def get_status(self, task_id: str):
        return self.tasks.get(task_id, {"status": "not_found"})

# Singleton
async_worker = AsyncWorker()
