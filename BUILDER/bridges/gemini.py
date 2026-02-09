"""
Gemini Bridge — file-based communication via INBOX/.
Gemini CLI picks up tasks through PULSE sync.
"""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from BUILDER.config import INBOX_DIR
from BUILDER.core.task_manager import Task

logger = logging.getLogger("builder.bridge.gemini")


class GeminiBridge:
    def __init__(self, inbox_dir: Path | None = None):
        self.inbox = inbox_dir or INBOX_DIR

    async def execute(self, task: Task) -> dict:
        """Write task to INBOX for Gemini PULSE to pick up."""
        self.inbox.mkdir(parents=True, exist_ok=True)

        filename = f"TASK_{task.id}_FOR_GEMINI.md"
        filepath = self.inbox / filename

        content = f"""# TASK {task.id}
## DLA: GEMINI_ARCHITECT
## OD: BUILDER
## PRIORYTET: {task.priority.upper()}
## OPIS: {task.title}
## KONTEKST: {task.description}
## KRYTERIA AKCEPTACJI: Task completed and result written to INBOX/RESULT_{task.id}_FROM_GEMINI.md
"""

        filepath.write_text(content, encoding="utf-8")
        logger.info(f"Wrote task to {filepath}")

        return {
            "success": True,
            "mode": "async_file",
            "file": str(filepath),
            "message": f"Task written to INBOX. Gemini PULSE will pick it up. Waiting for RESULT_{task.id}_FROM_GEMINI.md",
        }

    def check_result(self, task: Task) -> dict | None:
        """Check if Gemini has written a result file."""
        result_file = self.inbox / f"RESULT_{task.id}_FROM_GEMINI.md"
        if result_file.exists():
            content = result_file.read_text(encoding="utf-8")
            return {"success": True, "response": content}
        return None
