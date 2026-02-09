import os
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

logger = logging.getLogger("ARCHIVIST")

class Archivist:
    """
    🗄️ OMEGA ARCHIVIST
    Autonomously catalogs and tags external archives.
    Stores data in a Master Index database.
    """
    def __init__(self, db_path: str = "data/archive_index.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS archive_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE,
                filename TEXT,
                extension TEXT,
                size_bytes INTEGER,
                modified_at DATETIME,
                tags TEXT,
                summary TEXT,
                indexed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Index for fast search
        conn.execute("CREATE INDEX IF NOT EXISTS idx_filename ON archive_items(filename)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tags ON archive_items(tags)")
        conn.commit()
        conn.close()

    async def catalog_directory(self, root_path: str):
        """Recursively scans and indexes a directory."""
        root = Path(root_path).resolve()
        logger.info(f"🗄️ ARCHIVIST: Starting cataloging of {root}")
        
        conn = sqlite3.connect(self.db_path)
        count = 0
        
        for r, dirs, files in os.walk(root):
            for file in files:
                file_path = Path(r) / file
                try:
                    stat = file_path.stat()
                    ext = file_path.suffix.lower()
                    
                    # Basic tagging logic
                    tags = self._generate_basic_tags(file_path, ext)
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO archive_items 
                        (path, filename, extension, size_bytes, modified_at, tags)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        str(file_path),
                        file,
                        ext,
                        stat.st_size,
                        datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        ",".join(tags)
                    ))
                    
                    count += 1
                    if count % 100 == 0:
                        conn.commit()
                        logger.info(f"🗄️ Indexed {count} items...")
                        
                except Exception as e:
                    logger.error(f"❌ Failed to index {file_path}: {e}")
        
        conn.commit()
        conn.close()
        logger.info(f"🏁 ARCHIVIST: Cataloging complete. Total items: {count}")

    def _generate_basic_tags(self, path: Path, ext: str) -> List[str]:
        """Simple heuristic-based tagging."""
        tags = [ext.strip(".")]
        path_parts = path.parts
        
        # Add directory names as tags
        for part in path_parts[-4:-1]: # Last few directories
            if part and not part.startswith(("_", ".")):
                tags.append(part.lower())
        
        # Categorization
        if ext in [".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".c", ".cpp"]: tags.append("code")
        if ext in [".md", ".txt", ".pdf", ".doc", ".docx"]: tags.append("doc")
        if ext in [".jpg", ".png", ".gif", ".svg"]: tags.append("image")
        if ext in [".zip", ".rar", ".7z", ".gz"]: tags.append("archive")
        
        return list(set(tags))

archivist = Archivist()
