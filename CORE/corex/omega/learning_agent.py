import os
import logging
import asyncio
from pathlib import Path
from typing import List
from corex.memory_engine import memory_engine

logger = logging.getLogger(__name__)

class LearningAgent:
    """
    🧠 OMEGA LEARNING AGENT
    Autonomously crawls the codebase and environment to expand the Knowledge Base.
    Identifies patterns, dependencies, and architectural debt.
    """
    def __init__(self, root_dir: str = "."):
        self.root = Path(root_dir).resolve()
        self.ignored_dirs = [".git", "__pycache__", "node_modules", "data", "venv"]
        self.supported_extensions = [".py", ".md", ".json", ".txt", ".bat", ".ps1"]

    async def run_autonomous_learning(self):
        """
        Main loop for background learning.
        1. Scan for new/modified files.
        2. Extract structural insights.
        3. Index into Hybrid Memory.
        """
        logger.info("🧠 LEARNING AGENT: Commencing knowledge base expansion...")
        
        for file_path in self._crawl_workspace():
            try:
                # Basic indexing of file structure and purpose
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                if not content.strip(): continue

                summary = f"File: {file_path.name} | Path: {file_path.relative_to(self.root)}"
                # (In future, use local LLM to generate a real summary)
                
                await memory_engine.store_memory(
                    content=f"{summary}\nContent Snippet: {content[:500]}...",
                    category="codebase_structure",
                    importance=0.5,
                    metadata={"file_path": str(file_path)}
                )
                logger.info(f"✅ Learned: {file_path.name}")
                await asyncio.sleep(0.1) # Throttling to save resources
                
            except Exception as e:
                logger.error(f"❌ Learning failed for {file_path}: {e}")

        logger.info("🏁 LEARNING AGENT: Initial scan complete. Knowledge base expanded.")

    def _crawl_workspace(self) -> List[Path]:
        """Crawl the root directory for relevant files."""
        found_files = []
        for root, dirs, files in os.walk(self.root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.ignored_dirs]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    found_files.append(Path(root) / file)
        return found_files

learning_agent = LearningAgent()
