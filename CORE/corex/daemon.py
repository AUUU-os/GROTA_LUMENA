"""
CORE_X_AGENT Daemon
Main orchestration process
"""

import asyncio
import logging
import signal
from typing import Dict, Any, Optional
from datetime import datetime
import time

from .interpreter import CommandInterpreter
from .policy import PolicyEngine, PolicyDecision, WindowMode, PolicyContext
from .router import ModuleRouter
from .audit import AuditLogger
from .vault import SecretVault
from .error_formatter import ErrorFormatter
from .metrics import metrics_engine
from .evolution_hub import evolution_hub

# Lazy imports for modules to avoid circular deps
def get_sentinel_module():
    from modules.sentinel import SentinelModule
    return SentinelModule()

def get_architect_module(working_dir):
    from modules.architect import ArchitectModule
    return ArchitectModule(working_dir=working_dir)

logger = logging.getLogger(__name__)

class CoreXDaemon:
    def __init__(
        self,
        mode: WindowMode = WindowMode.DESIGN,
        data_dir: str = "data",
        working_dir: Optional[str] = None,
    ):
        self.mode = mode
        self.data_dir = data_dir
        self.working_dir = working_dir
        self.is_running = False

        self.interpreter = CommandInterpreter()
        self.policy = PolicyEngine(mode=mode)
        self.router = ModuleRouter()
        self.audit = AuditLogger(data_dir=f"{data_dir}/audit")
        self.vault = SecretVault(vault_dir=f"{data_dir}/vault")
        self.error_formatter = ErrorFormatter()

        self.stats = {
            "commands_total": 0,
            "commands_allowed": 0,
            "commands_denied": 0,
            "commands_failed": 0,
            "started_at": None,
        }
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        def signal_handler(sig, frame):
            logger.info(f"Received signal {sig}, shutting down...")
            asyncio.create_task(self.stop())
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def _init_modules(self) -> None:
        # Simplified for now
        logger.info("Initializing modules...")

    async def start(self) -> None:
        logger.info("CORE_X_AGENT starting...")
        await self.vault.initialize()
        await self._init_modules()
        
        asyncio.create_task(evolution_hub.monitor_and_evolve())
        asyncio.create_task(self._schedule_omega_refresh())

        self.stats["started_at"] = datetime.now().isoformat()
        self.is_running = True
        logger.info("CORE_X_AGENT started successfully")

    async def stop(self) -> None:
        self.is_running = False
        logger.info("CORE_X_AGENT stopped")

    async def _schedule_omega_refresh(self):
        """Schedules Full Knowledge Synchronization for 03:00 AM."""
        while self.is_running:
            now = datetime.now()
            if now.hour == 3 and now.minute == 0:
                from .memory_engine import memory_engine
                await memory_engine.batch_refresh()
                await asyncio.sleep(60)
            await asyncio.sleep(30)

    async def _adaptive_learning_feedback(self, command: str, response: Dict[str, Any]):
        pass

    async def execute_command(self, command: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        start_time = time.perf_counter()
        # Mock implementation for mining verification
        latency_ms = (time.perf_counter() - start_time) * 1000
        await evolution_hub.track_resonance(True, latency_ms)
        await evolution_hub.recursive_optimize()
        return {"success": True}

