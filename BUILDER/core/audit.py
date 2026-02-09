"""
AuditLog — logs all Builder operations to daily log files.
"""

import logging
from datetime import datetime
from pathlib import Path

from BUILDER.config import LOGS_DIR

logger = logging.getLogger("builder.audit")


class AuditLog:
    def __init__(self, logs_dir: Path | None = None):
        self._dir = logs_dir or LOGS_DIR
        self._dir.mkdir(parents=True, exist_ok=True)

    def log(
        self,
        action: str,
        agent: str = "-",
        task_id: str = "-",
        status: str = "ok",
        details: str = "",
    ):
        """Write audit entry to daily log file."""
        now = datetime.now()
        log_file = self._dir / f"{now.strftime('%Y-%m-%d')}.log"
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        line = f"{timestamp} | {action:<20} | {agent:<20} | {task_id:<14} | {status:<8} | {details}\n"

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(line)

        logger.debug(f"Audit: {action} | {agent} | {task_id} | {status}")

    def read_today(self, limit: int = 100) -> list[str]:
        """Read today's log entries."""
        log_file = self._dir / f"{datetime.now().strftime('%Y-%m-%d')}.log"
        if not log_file.exists():
            return []
        lines = log_file.read_text(encoding="utf-8").strip().split("\n")
        return lines[-limit:]

    def read_recent(self, limit: int = 50) -> list[str]:
        """Read most recent log entries across all days."""
        all_lines = []
        log_files = sorted(self._dir.glob("*.log"), reverse=True)
        for log_file in log_files:
            lines = log_file.read_text(encoding="utf-8").strip().split("\n")
            all_lines.extend(lines)
            if len(all_lines) >= limit:
                break
        return all_lines[:limit]
