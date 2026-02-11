"""
LUMEN MEMORY ENGINE
Handles parsing, serialization, vectorization, and hybrid retrieval.
Integrates SQL storage with ChromaDB vector search.
"""

import json
import logging
import os
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
            # corex/memory_engine.py -> corex -> CORE -> GROTA_LUMENA
            base = Path(__file__).resolve().parents[3]
        self.backup_dir = base / "DATABASE" / "memory_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    async def load(self):
        """Explicitly initialize resources (warm-up)."""
        logger.info("đźş Memory Engine: Loading...")
        # Force vector db initialization check (if applicable)
        # In future, this could preload embeddings or verify connection
        logger.info("âś… Memory Engine: READY")

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
        """
        Processes and stores a new memory entry.
        Steps: Parsing -> Validation -> Vectorization -> Indexing.
        """
        # 1. Parsing & Metadata preparation
        metadata = metadata or {}
        if session_id:
            metadata["session_id"] = session_id
        if agent_id:
            metadata["agent_id"] = agent_id
        metadata_str = json.dumps(metadata)
        safe_type = memory_type or "general"
        embedding_id = f"mem_{int(datetime.utcnow().timestamp())}_{safe_type}"

        # 2. Vectorization & ChromaDB Indexing
        # (This handles the embedding generation internally via SentenceTransformers)
        await self.vector_db.add_document(
            text=content,
            doc_id=embedding_id,
            metadata={"memory_type": safe_type, "importance": importance, **metadata},
        )

        # 3. SQL Serialization & Persistence
        async for session in get_session():
            new_entry = MemoryEntry(
                session_id=session_id,
                agent_id=agent_id,
                content=content,
                embedding_id=embedding_id,
                importance=int(importance),
                memory_type=safe_type,
                meta_data=json.loads(metadata_str),
            )
            session.add(new_entry)
            await session.commit()
            await session.refresh(new_entry)
            logger.info(f"Memory indexed: {embedding_id}")
            # Optional collective memory mirror
            if include_collective and agent_id and agent_id != "collective":
                try:
                    collective_id = f"{embedding_id}_collective"
                    await self.vector_db.add_document(
                        text=content,
                        doc_id=collective_id,
                        metadata={"memory_type": safe_type, "importance": importance, "agent_id": "collective", "source_agent": agent_id, **metadata},
                    )
                    collective_entry = MemoryEntry(
                        session_id=session_id,
                        agent_id="collective",
                        content=content,
                        embedding_id=collective_id,
                        importance=int(importance),
                        memory_type=safe_type,
                        meta_data={**json.loads(metadata_str), "source_agent": agent_id},
                    )
                    session.add(collective_entry)
                    await session.commit()
                except Exception as e:
                    logger.error(f"Collective memory mirror failed: {e}")
            return new_entry

    async def retrieve_memories(
        self,
        query: str,
        limit: int = 5,
        strategy: str = "hybrid",
        offset: int = 0,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieval Strategies: semantic, temporal, or hybrid.
        """
        if strategy == "semantic":
            return await self._semantic_retrieval(
                query, limit, offset=offset, agent_id=agent_id, session_id=session_id
            )
        elif strategy == "temporal":
            return await self._temporal_retrieval(
                limit, offset, agent_id=agent_id, session_id=session_id
            )
        else: # Default: hybrid
            return await self._hybrid_retrieval(
                query, limit, offset=offset, agent_id=agent_id, session_id=session_id
            )

    async def _semantic_retrieval(
        self,
        query: str,
        limit: int,
        offset: int = 0,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Pure similarity search via ChromaDB."""
        results = await self.vector_db.search(query, limit=limit)
        # Parse ChromaDB results into a clean list
        output = []
        if "documents" in results and results["documents"]:
            for i in range(len(results["documents"][0])):
                output.append({
                    "content": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        if agent_id or session_id:
            output = [
                r
                for r in output
                if (not agent_id or r.get("metadata", {}).get("agent_id") == agent_id)
                and (not session_id or r.get("metadata", {}).get("session_id") == session_id)
            ]
        if offset:
            output = output[offset:]
        return output[:limit]

    async def _temporal_retrieval(
        self,
        limit: int,
        offset: int = 0,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch most recent memories from SQL."""
        async for session in get_session():
            statement = (
                select(MemoryEntry)
                .order_by(MemoryEntry.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
            if agent_id:
                statement = statement.where(MemoryEntry.agent_id == agent_id)
            if session_id:
                statement = statement.where(MemoryEntry.session_id == session_id)
            result = await session.execute(statement)
            entries = result.scalars().all()
            return [e.model_dump() for e in entries]

    async def _hybrid_retrieval(
        self,
        query: str,
        limit: int,
        offset: int = 0,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Combines Semantic search with Importance weighting.
        """
        # Get semantic candidates
        semantic_results = await self._semantic_retrieval(
            query, limit=(limit * 2) + offset, offset=0, agent_id=agent_id, session_id=session_id
        )
        
        # In a real hybrid strategy, we would re-rank based on importance and recency
        # For now, we take the top semantic results and sort by combined score
        # (Assuming distance is cosine, smaller is better)
        for res in semantic_results:
            importance = res["metadata"].get("importance", 1.0)
            # Simple heuristic: score = (1-distance) * importance
            res["resonance_score"] = (1.0 - res["distance"]) * importance

        # Sort by resonance score descending
        hybrid_results = sorted(semantic_results, key=lambda x: x.get("resonance_score", 0), reverse=True)
        if offset:
            hybrid_results = hybrid_results[offset:]
        return hybrid_results[:limit]

    async def export_temporal(
        self,
        limit: int = 1000,
        offset: int = 0,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return await self.retrieve_memories(
            query="",
            limit=limit,
            strategy="temporal",
            offset=offset,
            agent_id=agent_id,
            session_id=session_id,
        )

    async def backup_to_file(
        self,
        limit: int = 1000,
        offset: int = 0,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        keep_days: int = 7,
    ) -> str:
        """Create a JSON backup file and enforce retention."""
        data = await self.export_temporal(limit, offset, agent_id, session_id)
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = self.backup_dir / f"memory_backup_{ts}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.cleanup_backups(keep_days=keep_days)
        return str(filename)

    def cleanup_backups(self, keep_days: int = 7) -> int:
        """Remove backups older than keep_days. Returns count removed."""
        removed = 0
        cutoff = datetime.utcnow().timestamp() - (keep_days * 86400)
        for p in self.backup_dir.glob("memory_backup_*.json"):
            try:
                if p.stat().st_mtime < cutoff:
                    p.unlink()
                    removed += 1
            except Exception:
                continue
        return removed


    async def auto_snap_loop(self, interval_seconds: int = 900):
        \"\"\"Background loop for periodic memory snapshots (Auto Snap).\"\"\"
        logger.info(f"đź“¸ Auto Snap: Loop started (Interval: {interval_seconds}s)")
        while True:
            try:
                await asyncio.sleep(interval_seconds)
                backup_path = await self.backup_to_file()
                logger.info(f"đź“¸ Auto Snap: Backup created at {backup_path}")
            except Exception as e:
                logger.error(f"đź“¸ Auto Snap: Error during backup: {e}")

    def start_auto_snap(self, interval_seconds: int = 900):
        \"\"\"Launch the auto snap loop in the current event loop.\"\"\"
        asyncio.create_task(self.auto_snap_loop(interval_seconds))

# Singleton instance
memory_engine = MemoryEngine()
