import json
import time
from pathlib import Path
from datetime import datetime

class NeuralMemory:
    def __init__(self, data_path: Path):
        self.file = data_path / "LONG_TERM.json"
        self.db = []
        self._load()

    def _load(self):
        if self.file.exists():
            try:
                self.db = json.loads(self.file.read_text(encoding='utf-8'))
            except: self.db = []

    def save(self):
        self.file.write_text(json.dumps(self.db, indent=2, ensure_ascii=False), encoding='utf-8')

    def inject(self, content, tags="auto"):
        engram = {"ts": datetime.now().isoformat(), "content": content, "tags": tags}
        self.db.append(engram)
        self.save()

    def recall(self, query):
        q = query.lower().split()
        # Zwraca 5 ostatnich pasujących wspomnień
        hits = [m for m in self.db if any(w in m['content'].lower() for w in q)]
        return hits[-5:] if hits else []