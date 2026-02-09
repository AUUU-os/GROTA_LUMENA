"""
Claude Bridge — file-based communication via INBOX/.
Claude Code is CLI-based, so we communicate by writing task files
and watching for result files.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from BUILDER.config import INBOX_DIR
from BUILDER.core.task_manager import Task

logger = logging.getLogger("builder.bridge.claude")


class ClaudeBridge:
    def __init__(self, inbox_dir: Path | None = None):
        self.inbox = inbox_dir or INBOX_DIR

    async def execute(self, task: Task) -> dict:
        """Write task to INBOX for Claude to pick up.

        This is async in the sense that it writes the file and returns.
        Actual result comes back through FileWatcher when Claude
        writes RESULT_xxx_FROM_CLAUDE.md.
        """
        self.inbox.mkdir(parents=True, exist_ok=True)

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"TASK_{task.id}_FOR_CLAUDE.md"
        filepath = self.inbox / filename

        content = f"""# TASK {task.id}
## DLA: CLAUDE_LUSTRO
## OD: BUILDER
## PRIORYTET: {task.priority.upper()}
## OPIS: {task.title}
## KONTEKST: {task.description}
## KRYTERIA AKCEPTACJI: Task completed and result written to INBOX/RESULT_{task.id}_FROM_CLAUDE.md
"""

        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Wrote task to {filepath}")

        return {
            "success": True,
            "mode": "async_file",
            "file": str(filepath),
            "message": f"Task written to INBOX. Waiting for RESULT_{task.id}_FROM_CLAUDE.md",
        }

    def check_result(self, task: Task) -> dict | None:
        """Check if Claude has written a result file."""
        result_file = self.inbox / f"RESULT_{task.id}_FROM_CLAUDE.md"
        if result_file.exists():
            content = result_file.read_text(encoding="utf-8")
            return {"success": True, "response": content}
        return None
