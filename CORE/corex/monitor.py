"""
LUMEN RESOURCE MONITOR (LDP v2.0)
Real-time system health and resonance tracking.
"""

import psutil
import time
import asyncio
from datetime import datetime
from typing import Dict, Any

class ResourceMonitor:
    def __init__(self):
        self.boot_time = datetime.now()
        self._last_db_check = 0
        self._db_latency = 0.0

    def get_system_stats(self) -> Dict[str, float]:
        return {
            "cpu_usage": psutil.cpu_percent(interval=None),
            "ram_usage": psutil.virtual_memory().percent,
            "boot_time": self.boot_time.isoformat()
        }

    async def check_db_health(self):
        """Asynchroniczne sprawdzanie bazy (symulacja/ping)."""
        # W pełnej wersji tutaj byłby `SELECT 1` do bazy
        # Na potrzeby monitora, mierzymy czas dostępu do pliku DB
        try:
            start = time.time()
            # Placeholder for async DB ping via SQLAlchemy
            await asyncio.sleep(0.001) 
            self._db_latency = (time.time() - start) * 1000
        except Exception:
            self._db_latency = -1.0

    def get_pulse(self) -> Dict[str, Any]:
        """Agregacja wszystkich metryk."""
        stats = self.get_system_stats()
        
        status = "OPERATIONAL"
        if stats["cpu_usage"] > 90 or stats["ram_usage"] > 90:
            status = "DEGRADED"
        if self._db_latency < 0:
            status = "CRITICAL"

        return {
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
            "cpu_usage": stats["cpu_usage"],
            "ram_usage": stats["ram_usage"],
            "db_latency": round(self._db_latency, 2)
        }

resource_monitor = ResourceMonitor()