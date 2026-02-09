import json
import os
import time
from datetime import datetime

class ReportGenerator:
    """
    Generates consolidated reports for LUMEN CORE v18.0
    """
    def __init__(self, output_dir="logs"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate_report(self, voice_manager, memory_module, daemon_stats=None):
        """
        Consolidates metrics from Voice, Memory, and Daemon
        """
        uptime = "N/A"
        if daemon_stats and daemon_stats.get("started_at"):
            start_time = datetime.fromisoformat(daemon_stats["started_at"])
            uptime = str(datetime.now() - start_time)

        report = {
            "timestamp": datetime.now().isoformat(),
            "protocol": "LUMEN_CORE",
            "version": "v18.0",
            "mode": "production",
            "metrics": {
                "voice": {
                    "status": voice_manager.status,
                    "is_running": voice_manager.is_running,
                    "last_log": voice_manager.last_log
                },
                "memory": {
                    "is_running": memory_module.is_running,
                    "operations_count": memory_module.operations_count,
                    "storage_file": memory_module.memory.state_file
                },
                "system": {
                    "uptime": uptime,
                    "log_level": "INFO",
                    "daemon_stats": daemon_stats or {}
                }
            }
        }
        
        filename = f"LUMEN_CORE_REPORT_{int(time.time())}.json"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4)
            
        return filepath, report

# Usage helper
if __name__ == "__main__":
    print("Report Generator Tool")
