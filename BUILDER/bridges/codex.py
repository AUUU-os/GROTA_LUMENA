"""
Codex Bridge — executes tasks via codex_task.ps1.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

from BUILDER.config import GROTA_ROOT, INBOX_DIR
from BUILDER.core.task_manager import Task

logger = logging.getLogger("builder.bridge.codex")

CODEX_SCRIPT = GROTA_ROOT / "APP" / "codex_task.ps1"


class CodexBridge:
    def __init__(self):
        self.inbox = INBOX_DIR

    async def execute(self, task: Task) -> dict:
        """Execute task via Codex using codex_task.ps1."""
        if not CODEX_SCRIPT.exists():
            return {"success": False, "error": f"codex_task.ps1 not found at {CODEX_SCRIPT}"}

        prompt = f"{task.title}: {task.description}"

        try:
            proc = await asyncio.create_subprocess_exec(
                "powershell", "-ExecutionPolicy", "Bypass", "-File",
                str(CODEX_SCRIPT), prompt, str(GROTA_ROOT),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)

            if proc.returncode == 0:
                return {
                    "success": True,
                    "mode": "async_file",
                    "message": "Codex task launched. Result will appear in INBOX/CODEX_RESULT_*.md",
                    "stdout": stdout.decode("utf-8", errors="replace"),
                }
            else:
                return {
                    "success": False,
                    "error": stderr.decode("utf-8", errors="replace"),
                }
        except asyncio.TimeoutError:
            return {"success": False, "error": "Codex execution timed out (300s)"}
        except Exception as e:
            logger.error(f"Codex bridge error: {e}")
            return {"success": False, "error": str(e)}
