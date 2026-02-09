import logging
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)


class VectorMemory:
    """
    Semantic Memory Engine using ChromaDB.
    Provides vector embeddings and similarity search.
    Lazy-initialized: heavy dependencies (torch, sentence-transformers) load on first use.
    """

    def __init__(self, db_path: str = "data/vector_db"):
        self.db_path = db_path
        self._client = None
        self._embed_fn = None
        self._collection = None

    def _ensure_initialized(self):
        """Lazy init — loads chromadb + sentence-transformers on first use."""
        if self._collection is not None:
            return
        import chromadb
        from chromadb.utils import embedding_functions

        os.makedirs(self.db_path, exist_ok=True)
        self._client = chromadb.PersistentClient(path=self.db_path)
        self._embed_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        self._collection = self._client.get_or_create_collection(
            name="lumen_knowledge",
            embedding_function=self._embed_fn,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("VectorMemory initialized (lazy)")

    @property
    def collection(self):
        self._ensure_initialized()
        return self._collection

    async def add_document(
        self, text: str, doc_id: str, metadata: Dict[str, Any] = None
    ):
        """Add text to vector store"""
        try:
            self.collection.add(
                documents=[text], ids=[doc_id], metadatas=[metadata or {}]
            )
            logger.info(f"indexed document: {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            return False

    async def search(self, query: str, limit: int = 5) -> Dict[str, Any]:
        """Perform semantic search"""
        try:
            results = self.collection.query(query_texts=[query], n_results=limit)
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {"error": str(e)}

    def get_stats(self):
        if self._collection is None:
            return {"count": 0, "db_path": self.db_path, "initialized": False}
        return {
            "count": self.collection.count(),
            "db_path": self.db_path,
            "initialized": True,
        }


# Singleton instance
vector_memory = VectorMemory()
