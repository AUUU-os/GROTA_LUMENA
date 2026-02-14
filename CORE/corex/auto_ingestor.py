import os
import time
import logging
import asyncio
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from .memory_engine import memory_engine

logger = logging.getLogger("AUTO-INGESTOR")

class GrottoFileHandler(FileSystemEventHandler):
    def __init__(self, target_folders):
        self.target_folders = target_folders
        self.last_processed = {}

    def on_modified(self, event):
        if not event.is_directory:
            asyncio.run_coroutine_threadsafe(self._process_file(event.src_path), asyncio.get_event_loop())

    def on_created(self, event):
        if not event.is_directory:
            asyncio.run_coroutine_threadsafe(self._process_file(event.src_path), asyncio.get_event_loop())

    async def _process_file(self, file_path):
        now = time.time()
        if file_path in self.last_processed and now - self.last_processed[file_path] < 5:
            return
        
        ext = Path(file_path).suffix.lower()
        # Ignored paths
        if any(ignored in file_path for ignored in ['.git', '__pycache__', 'node_modules', '.gemini']):
            return

        if ext in ['.md', '.txt', '.py', '.json', '.yaml']:
            logger.info(f"âşş Ingesting: {file_path}")
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                await memory_engine.store_memory(
                    content=content,
                    memory_type="file_ingest",
                    importance=7,
                    metadata={"path": file_path, "filename": Path(file_path).name}
                )
                self.last_processed[file_path] = now
            except Exception as e:
                logger.error(f"Error ingesting {file_path}: {e}")

class AutoIngestor:
    def __init__(self, folders_to_watch=None):
        if folders_to_watch is None:
            base = Path(__file__).resolve().parents[2]
            folders_to_watch = [str(base)]
        self.folders = folders_to_watch
        self.observer = Observer()

    def start(self):
        handler = GrottoFileHandler(self.folders)
        for folder in self.folders:
            if os.path.exists(folder):
                self.observer.schedule(handler, folder, recursive=True)
                logger.info(f"đźŚş Watching folder: {folder}")
        self.observer.start()

    def stop(self):
        self.observer.stop()
        self.observer.join()

auto_ingestor = AutoIngestor()
