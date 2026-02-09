"""
Audit Logger
Persistent JSONL logging of all actions
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class AuditEntry:
    """Single audit log entry"""
    timestamp: str
    action: str
    intent: Dict[str, Any]
    policy_decision: str  # "allowed" | "denied"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {k: v for k, v in asdict(self).items() if v is not None}


import json
import os
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

# ... (AuditEntry remains same)

class AuditLogger:
    """
    Asynchronous JSONL audit logger
    """

    def __init__(self, data_dir: str = "data/audit"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file(self) -> Path:
        """Get current log file (daily rotation)"""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.data_dir / f"audit_{today}.jsonl"

    async def log(
        self,
        action: str,
        intent: Dict[str, Any],
        policy_decision: str,
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an action asynchronously."""
        entry = AuditEntry(
            timestamp=datetime.now().isoformat(),
            action=action,
            intent=intent,
            policy_decision=policy_decision,
            result=result,
            error=error,
            metadata=metadata
        )

        log_file = self._get_log_file()
        line = json.dumps(entry.to_dict()) + '\n'
        await asyncio.to_thread(self._append_line, log_file, line)

    def _append_line(self, file_path: Path, line: str):
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(line)

    async def query(
        self,
        action: Optional[str] = None,
        policy_decision: Optional[str] = None,
        date: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query audit logs asynchronously."""
        return await asyncio.to_thread(self._query_sync, action, policy_decision, date, limit)

    def _query_sync(self, action, policy_decision, date, limit):
        # (Internal sync query logic moved here)
        files = []
        if not date:
            master = self.data_dir / "MASTER_CHRONICLE.jsonl"
            if master.exists(): files.append(master)
        
        if date:
            log_file = self.data_dir / f"audit_{date}.jsonl"
            if log_file.exists(): files.append(log_file)
        else:
            daily_files = sorted(self.data_dir.glob("audit_*.jsonl"), reverse=True)
            files.extend(daily_files)

        results = []
        for log_file in files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if len(results) >= limit: return results
                    try: entry = json.loads(line.strip())
                    except: continue
                    if action and entry.get("action") != action: continue
                    if policy_decision and entry.get("policy_decision") != policy_decision: continue
                    results.append(entry)
        return results[:limit]

    def get_recent(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent entries"""
        return self.query(limit=limit)

    def get_stats(self, date: Optional[str] = None) -> Dict[str, Any]:
        """
        Get audit statistics

        Returns:
            Dictionary with counts by action and decision
        """
        entries = self.query(date=date, limit=10000)

        stats = {
            "total": len(entries),
            "by_action": {},
            "by_decision": {},
            "errors": 0
        }

        for entry in entries:
            action = entry.get("action", "unknown")
            decision = entry.get("policy_decision", "unknown")

            stats["by_action"][action] = stats["by_action"].get(action, 0) + 1
            stats["by_decision"][decision] = stats["by_decision"].get(decision, 0) + 1

            if entry.get("error"):
                stats["errors"] += 1

        return stats


# Example usage
if __name__ == "__main__":
    logger = AuditLogger()

    # Log allowed action
    logger.log(
        action="git_commit",
        intent={"command": "commit my changes", "files": ["main.py"]},
        policy_decision="allowed",
        result={"commit_hash": "abc123", "message": "feat: add new feature"}
    )

    # Log denied action
    logger.log(
        action="file_delete",
        intent={"command": "delete all files"},
        policy_decision="denied",
        metadata={"reason": "Destructive action not allowed in DESIGN mode"}
    )

    # Query recent
    recent = logger.get_recent(limit=5)
    print(f"Recent entries: {len(recent)}")
    for entry in recent:
        print(f"  {entry['timestamp']}: {entry['action']} - {entry['policy_decision']}")

    # Get stats
    stats = logger.get_stats()
    print(f"\nStats: {stats}")
