import aiosqlite
import logging
import os
import asyncio
from typing import Optional

logger = logging.getLogger("DB_CORE")

class DatabaseManager:
    """
    OMEGA UPGRADE: Async SQLite (aiosqlite).
    Non-blocking, WAL-enabled data persistence.
    """
    def __init__(self, db_path="data/lumen_core.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

    async def init_db(self):
        """Asynchronous database initialization."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # WAL Mode for high concurrency
                await db.execute("PRAGMA journal_mode=WAL;")
                await db.execute("PRAGMA synchronous=NORMAL;")
                
                # Table Reconstruction
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        type TEXT,
                        payload TEXT
                    )
                """)
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        name TEXT,
                        value REAL
                    )
                """)
                await db.commit()
                logger.info(f"💾 ASYNC DB INITIALIZED: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ ASYNC DB INIT FAILED: {e}")

    async def log_event(self, event_type: str, payload: str):
        """Asynchronous event logging."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO events (type, payload) VALUES (?, ?)", 
                    (event_type, payload)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"❌ Event log failed: {e}")

    async def log_metric(self, name: str, value: float):
        """Asynchronous metric persistence."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO metrics (name, value) VALUES (?, ?)", 
                    (name, value)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"❌ Metric log failed: {e}")

# Singleton
db_manager = DatabaseManager()
