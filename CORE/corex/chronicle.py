"""
LUMEN CHRONICLE (Wrapper)
Aligns existing AuditLogger with the new technical manifest.
"""

from .audit import AuditLogger
from datetime import datetime
import json

class Chronicle:
    def __init__(self, data_dir="data/audit"):
        self.logger = AuditLogger(data_dir=data_dir)

    def save(self, event: str):
        self.logger.log(
            action="CHRONICLE_SAVE",
            intent={"operation": "manual_save", "module": "chronicle"},
            policy_decision="allowed",
            result={"event": event}
        )
        return {"status": "saved", "event": event}

    def search(self, query: str = None, limit: int = 100):
        entries = self.logger.query(action="CHRONICLE_SAVE", limit=limit)
        if query:
            entries = [e for e in entries if query.lower() in str(e).lower()]
        return {
            "entries": entries,
            "total": len(entries)
        }

    def checkpoint(self):
        ts = datetime.utcnow().isoformat()
        self.logger.log(
            action="CHRONICLE_CHECKPOINT",
            intent={"operation": "checkpoint", "module": "chronicle"},
            policy_decision="allowed",
            result={"timestamp": ts}
        )
        return {
            "status": "checkpoint_created",
            "timestamp": ts
        }

# Singleton
chronicle = Chronicle()
