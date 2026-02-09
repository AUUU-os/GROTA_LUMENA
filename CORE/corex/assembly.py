"""
LUMEN SYSTEM ASSEMBLY
"""

import asyncio
import logging
from typing import Dict, Any

from .daemon import CoreXDaemon, WindowMode
from .vector_memory import vector_memory
from .audit import AuditLogger
from .resonance_physics import resonance_engine
from .evolution_engine import evolution_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LUMEN_ASSEMBLY")

class LumenSystem:
    def __init__(self):
        self.daemon = None
        self.memory = vector_memory
        self.audit = AuditLogger()
        self.resonance = resonance_engine
        self.evolution = evolution_engine
        self.status = "OFFLINE"

    async def assemble(self):
        logger.info("Starting LUMEN SYSTEM ASSEMBLY...")
        
        self.daemon = CoreXDaemon(mode=WindowMode.DESIGN, data_dir="data")
        await self.daemon.start()
        
        stats = self.memory.get_stats()
        logger.info(f"Memory Engine: ONLINE ({stats['count']} docs)")
        
        recent = self.audit.get_recent(limit=1)
        if recent:
            logger.info("Chronicle: ESTABLISHED")
        else:
            logger.warning("Chronicle: EMPTY")

        res_state = self.resonance.calculate_current_resonance(963.0)
        logger.info(f"Resonance: TUNED (A={res_state.amplitude})")

        self.status = "OPERATIONAL"
        logger.info("SYSTEM ASSEMBLY COMPLETE.")

    def get_system_report(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "organs": {
                "daemon": self.daemon.get_status() if self.daemon else "OFFLINE",
                "memory": self.memory.get_stats(),
                "resonance": 963.0,
                "history_depth": len(self.audit.query(limit=10000))
            }
        }

async def main():
    lumen = LumenSystem()
    await lumen.assemble()
    report = lumen.get_system_report()
    print("LUMEN ASSEMBLY REPORT")
    print(f"Status: {report['status']}")
    print(f"History Depth: {report['history_depth']} events")

if __name__ == "__main__":
    asyncio.run(main())