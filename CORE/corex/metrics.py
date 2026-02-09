import time
import psutil
import logging
from typing import Dict, Any
from datetime import datetime
from prometheus_client import Counter, Gauge, Histogram, Summary

logger = logging.getLogger(__name__)

# Prometheus Metrics
COMMANDS_TOTAL = Counter('lumen_commands_total', 'Total number of commands processed', ['module', 'operation', 'success'])
LATENCY_SUMMARY = Summary('lumen_command_latency_seconds', 'Latency of command execution in seconds')
RESOURCE_USAGE = Gauge('lumen_resource_usage', 'System resource utilization', ['resource'])
RESONANCE_SCORE = Gauge('lumen_resonance_score', 'Current system resonance score')

class MetricsEngine:
    """
    LEX XI-PLUS 6.0 ULTRA Performance Monitoring.
    Tracks latency, throughput, and resource utilization with Prometheus support.
    """
    def __init__(self):
        self.start_time = time.time()
        self.commands_processed = 0
        self.errors_count = 0
        self.latency_history = []

    def log_command(self, module: str, operation: str, latency_ms: float, success: bool):
        self.commands_processed += 1
        if not success:
            self.errors_count += 1
        self.latency_history.append(latency_ms)
        
        # Prometheus updates
        COMMANDS_TOTAL.labels(module=module, operation=operation, success=str(success)).inc()
        LATENCY_SUMMARY.observe(latency_ms / 1000.0)
        
        # Keep last 100 for local KPI report
        self.latency_history = self.latency_history[-100:]

    def update_resource_metrics(self):
        """Update Prometheus gauges with system stats"""
        RESOURCE_USAGE.labels(resource='cpu').set(psutil.cpu_percent())
        RESOURCE_USAGE.labels(resource='memory').set(psutil.Process().memory_info().rss / 1024 / 1024)

    def get_kpis(self) -> Dict[str, Any]:
        avg_latency = sum(self.latency_history) / len(self.latency_history) if self.latency_history else 0
        uptime = time.time() - self.start_time
        
        # Format uptime
        hours, rem = divmod(int(uptime), 3600)
        minutes, seconds = divmod(rem, 60)
        uptime_str = f"{hours:02}:{minutes:02}:{seconds:02}"
        
        return {
            "uptime": uptime_str,
            "uptime_seconds": int(uptime),
            "throughput": round((self.commands_processed / (uptime / 60)) if uptime > 0 else 0, 2),
            "error_rate": round((self.errors_count / self.commands_processed * 100) if self.commands_processed > 0 else 0, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "resource_utilization": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_mb": round(psutil.Process().memory_info().rss / 1024 / 1024, 1)
            }
        }

# Singleton
metrics_engine = MetricsEngine()
