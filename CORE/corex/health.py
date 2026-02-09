"""
LUMEN Deep Health Check System v19.0
Comprehensive health monitoring: Ollama, disk, memory, CPU, modules.
"""

import shutil
import psutil
import time
import logging
from typing import Dict, Any

from corex.ollama_bridge import ollama_bridge
from corex.monitor import resource_monitor

logger = logging.getLogger("LUMEN")


class HealthChecker:
    """Aggregated deep health check for all system components."""

    def __init__(self):
        self._component_status: Dict[str, str] = {}

    async def check_ollama(self) -> Dict[str, Any]:
        """Check Ollama connectivity and list available models."""
        try:
            models = await ollama_bridge.get_models()
            if models:
                return {
                    "status": "healthy",
                    "models": models,
                    "model_count": len(models),
                }
            return {"status": "degraded", "models": [], "model_count": 0}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "models": []}

    def check_disk(self, path: str = "E:\\") -> Dict[str, Any]:
        """Check disk space on target drive."""
        try:
            usage = shutil.disk_usage(path)
            free_gb = usage.free / (1024**3)
            total_gb = usage.total / (1024**3)
            used_pct = (usage.used / usage.total) * 100

            status = "healthy"
            if used_pct > 90:
                status = "critical"
            elif used_pct > 80:
                status = "degraded"

            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "total_gb": round(total_gb, 2),
                "used_percent": round(used_pct, 1),
            }
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    def check_memory(self) -> Dict[str, Any]:
        """Check system RAM usage."""
        mem = psutil.virtual_memory()
        status = "healthy"
        if mem.percent > 90:
            status = "critical"
        elif mem.percent > 80:
            status = "degraded"

        return {
            "status": status,
            "used_percent": mem.percent,
            "available_gb": round(mem.available / (1024**3), 2),
            "total_gb": round(mem.total / (1024**3), 2),
        }

    def check_cpu(self) -> Dict[str, Any]:
        """Check CPU usage."""
        cpu_pct = psutil.cpu_percent(interval=None)
        status = "healthy"
        if cpu_pct > 90:
            status = "critical"
        elif cpu_pct > 80:
            status = "degraded"

        return {
            "status": status,
            "usage_percent": cpu_pct,
            "core_count": psutil.cpu_count(),
        }

    async def deep_check(self) -> Dict[str, Any]:
        """Run all health checks and aggregate results."""
        start = time.time()

        ollama = await self.check_ollama()
        disk = self.check_disk()
        memory = self.check_memory()
        cpu = self.check_cpu()
        pulse = resource_monitor.get_pulse()

        components = {
            "ollama": ollama,
            "disk": disk,
            "memory": memory,
            "cpu": cpu,
        }

        # Aggregate overall status
        statuses = [c.get("status", "unknown") for c in components.values()]
        if "critical" in statuses or "unhealthy" in statuses:
            overall = "CRITICAL"
        elif "degraded" in statuses:
            overall = "DEGRADED"
        else:
            overall = "OPERATIONAL"

        self._component_status = {k: v["status"] for k, v in components.items()}

        return {
            "status": overall,
            "check_duration_ms": round((time.time() - start) * 1000, 1),
            "components": components,
            "pulse": pulse,
        }


health_checker = HealthChecker()
