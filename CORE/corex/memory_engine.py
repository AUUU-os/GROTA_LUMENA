"""
LUMEN MEMORY ENGINE
Handles parsing, serialization, vectorization, and hybrid retrieval.
Integrates SQL storage with ChromaDB vector search.
"""

import json
import logging
import os
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import select
from .database.session import engine, get_session
from .database.models import MemoryEntry
from .vector_memory import vector_memory
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

class MemoryEngine:
    """
    Advanced Memory Management System for LUMEN v18.0.
    """
    def __init__(self):
        self.vector_db = vector_memory
        repo_root = os.getenv("LUMEN_REPO_ROOT")
        if repo_root:
            base = Path(repo_root)
        else:
            base = Path(__file__).resolve().parents[3]
        self.backup_dir = base / "DATABASE" / "memory_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def load(self):
        logger.info("Memory Engine: Loading...")
        logger.info("Memory Engine: READY")

    async def store_memory(
        self,
        content: str,
        memory_type: str = "general",
        importance: int = 5,
        metadata: Dict[str, Any] = None,
        session_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        include_collective: bool = True,
    ) -> MemoryEntry:
        metadata = metadata or {}
        if session_id: metadata["session_id"] = session_id
        if agent_id: metadata["agent_id"] = agent_id
        metadata_str = json.dumps(metadata)
        embedding_id = f"mem_{int(datetime.utcnow().timestamp())}_{memory_type}"

        await self.vector_db.add_document(
            text=content,
            doc_id=embedding_id,
            metadata={"memory_type": memory_type, "importance": importance, **metadata}
        )

        async for session in get_session():
            new_entry = MemoryEntry(
                session_id=session_id,
                agent_id=agent_id,
                content=content,
                embedding_id=embedding_id,
                importance=importance,
                memory_type=memory_type,
                meta_data=metadata
            )
            session.add(new_entry)
            await session.commit()
            await session.refresh(new_entry)
            logger.info(f"Memory indexed: {embedding_id}")
            return new_entry

    async def retrieve_memories(self, query: str, limit: int = 5, strategy: str = "hybrid"):
        results = await self.vector_db.search(query, limit=limit)
        output = []
        if "documents" in results and results["documents"]:
            for i in range(len(results["documents"][0])):
                output.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        return output

    async def batch_refresh(self):
        """Full Knowledge Refresh: Re-indexes files and evolves schema."""
        logger.info("OMEGA REFRESH: Starting Full Knowledge Synchronization...")
        from .database.schema_evolver import schema_evolver
        await schema_evolver.evolve_schema()
        logger.info("OMEGA REFRESH: Database and Knowledge Graph stabilized.")

    async def backup_to_file(self, keep_days: int = 7) -> str:
        """Create a JSON backup file and enforce retention."""
        async for session in get_session():
            statement = select(MemoryEntry).order_by(MemoryEntry.created_at.desc()).limit(1000)
            result = await session.execute(statement)
            data = [e.model_dump() for e in result.scalars().all()]
            ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = self.backup_dir / f"memory_backup_{ts}.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            self.cleanup_backups(keep_days=keep_days)
            return str(filename)

    def cleanup_backups(self, keep_days: int = 7) -> int:
        removed = 0
        cutoff = datetime.utcnow().timestamp() - (keep_days * 86400)
        for p in self.backup_dir.glob("memory_backup_*.json"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            except Exception: continue
        return removed

    async def auto_snap_loop(self, interval_seconds: int = 900):
        logger.info(f"Auto Snap: Loop started (Interval: {interval_seconds}s)")
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                path = await self.backup_to_file()
                logger.info(f"Auto Snap: Backup created at {path}")
            except Exception as e:
                logger.error(f"Auto Snap Error: {e}")

    def start_auto_snap(self, interval_seconds: int = 900):
        asyncio.create_task(self.auto_snap_loop(interval_seconds))

# Singleton instance
memory_engine = MemoryEngine()
