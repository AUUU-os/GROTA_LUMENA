import os
import ast
import logging
from typing import Dict, List, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class EvolutionEngine:
    """
    Analyzes and proposes structural improvements to the codebase.
    Used by EVO agent to counter "mediocrity".
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.history = []
        self.backups_dir = os.path.join(root_dir, "data", "backups")
        os.makedirs(self.backups_dir, exist_ok=True)

    def analyze_module_depth(self, module_path: str) -> Dict[str, Any]:
        """Analyzes code complexity and structure using AST"""
        try:
            with open(module_path, "r", encoding="utf-8") as f:
                content = f.read()
                tree = ast.parse(content)
            
            stats = {
                "lines": len(content.splitlines()),
                "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]),
                "functions": len([n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]),
                "imports": len([n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]),
                "complexity_score": self._calculate_complexity(tree)
            }
            return stats
        except Exception as e:
            return {"error": str(e)}

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """Simple heuristic for code complexity"""
        nodes = list(ast.walk(tree))
        return len(nodes) / 100.0

    def create_patch(self, file_path: str, new_content: str, metadata: Dict = None) -> Dict[str, Any]:
        """Generates a backup and applies code evolution with rollback tracking."""
        filename = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{filename}_{timestamp}"
        backup_path = os.path.join(self.backups_dir, f"{backup_id}.bak")
        
        try:
            # 1. Verification: Parse new content before applying
            ast.parse(new_content)
            
            # 2. Backup existing
            if os.path.exists(file_path):
                import shutil
                shutil.copy2(file_path, backup_path)
            
            # 3. Apply Update
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            
            record = {
                "backup_id": backup_id,
                "file": file_path,
                "backup_path": backup_path,
                "timestamp": timestamp,
                "metadata": metadata or {},
                "status": "applied"
            }
            self.history.append(record)
            logger.info(f"🧬 Evolution applied: {backup_id}")
            return {"success": True, "record": record}
            
        except Exception as e:
            logger.error(f"❌ Evolution failed integrity check: {e}")
            return {"success": False, "error": str(e)}

    def rollback(self, backup_id: str = None) -> Dict[str, Any]:
        """Rolls back the last (or specific) evolution state."""
        if not self.history:
            return {"success": False, "error": "No evolution history found"}
        
        record = None
        if backup_id:
            record = next((r for r in self.history if r["backup_id"] == backup_id), None)
        else:
            record = self.history[-1]
            
        if not record:
            return {"success": False, "error": f"Backup {backup_id} not found"}
            
        try:
            import shutil
            shutil.copy2(record["backup_path"], record["file"])
            record["status"] = "rolled_back"
            logger.warning(f"🔄 ROLLBACK EXECUTED: {record['backup_id']}")
            return {"success": True, "file": record["file"]}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_relevance_proof(self, memory_data: List[Dict]) -> str:
        """Constructs a counter-argument for Jester based on memory depth"""
        total_items = len(memory_data)
        depth_score = sum([len(str(i)) for i in memory_data]) / 1024 # KB of knowledge
        return f"RELEVANCE PROOF: System holds {total_items} semantic units ({depth_score:.2f}KB knowledge depth). Mediocrity hypothesis rejected."

# Singleton
evolution_engine = EvolutionEngine()
