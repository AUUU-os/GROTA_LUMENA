"""
FileWatcher — monitors INBOX/ and M-AI-SELF/ for changes.
Uses watchdog library for cross-platform file system events.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from BUILDER.config import INBOX_DIR, M_AI_SELF_DIR

logger = logging.getLogger("builder.watcher")


class InboxHandler(FileSystemEventHandler):
    """Handles new files in INBOX/ directory."""

    def __init__(self, on_new_file: Callable[[Path], None]):
        self._callback = on_new_file

    def on_created(self, event: FileCreatedEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() == ".md":
            logger.info(f"New INBOX file: {path.name}")
            self._callback(path)


class StateHandler(FileSystemEventHandler):
    """Handles STATE.log changes in M-AI-SELF/."""

    def __init__(self, on_state_change: Callable[[Path], None]):
        self._callback = on_state_change

    def on_modified(self, event: FileModifiedEvent):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.name == "STATE.log":
            logger.info(f"Agent state changed: {path.parent.name}")
            self._callback(path)


class FileWatcher:
    def __init__(
        self,
        on_inbox_file: Callable[[Path], None] | None = None,
        on_state_change: Callable[[Path], None] | None = None,
    ):
        self._observer = Observer()
        self._on_inbox = on_inbox_file or (lambda p: None)
        self._on_state = on_state_change or (lambda p: None)

    def start(self):
        """Start watching INBOX/ and M-AI-SELF/."""
        if INBOX_DIR.exists():
            self._observer.schedule(
                InboxHandler(self._on_inbox),
                str(INBOX_DIR),
                recursive=False,
            )
            logger.info(f"Watching INBOX: {INBOX_DIR}")

        if M_AI_SELF_DIR.exists():
            self._observer.schedule(
                StateHandler(self._on_state),
                str(M_AI_SELF_DIR),
                recursive=True,
            )
            logger.info(f"Watching M-AI-SELF: {M_AI_SELF_DIR}")

        self._observer.start()
        logger.info("FileWatcher started")

    def stop(self):
        self._observer.stop()
        self._observer.join()
        logger.info("FileWatcher stopped")
