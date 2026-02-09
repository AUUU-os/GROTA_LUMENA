import json
import os
import aiofiles
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class LumenMemory:
    """
    LUMEN 10-Layer Memory System (Ported from LUMAVERSE OS v1)
    
    Layers:
    1. raw_input_buffer: All raw inputs
    2. short_term: Active conversation
    3. working_context: Current focus
    4. episodic: Event history
    5. semantic_long_term: Facts & Knowledge
    6. preferences_profile: User/Agent profiles
    7. tasks_state: Active TODOs
    8. projects_state: Project tracking
    9. meta_memory: Self-reflection & Stats
    10. archive: Cold storage
    """

    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.state_file = os.path.join(data_dir, "lumen_memory_v18.json")
        self.state: Dict[str, Any] = self._get_default_state()

    def _get_default_state(self) -> Dict[str, Any]:
        return {
            "schema_version": 1,
            "layers": {
                "raw_input_buffer": {"items": []},
                "short_term": {"items": []},
                "working_context": {"items": []},
                "episodic": {"items": []},
                "semantic_long_term": {"items": []},
                "preferences_profile": {},
                "tasks_state": {"items": []},
                "projects_state": {"items": []},
                "meta_memory": {"stats": {}, "rules": []},
                "archive": {"items": []}
            }
        }

    async def load(self):
        """Load state from file"""
        if os.path.exists(self.state_file):
            try:
                async with aiofiles.open(self.state_file, mode='r', encoding='utf-8') as f:
                    content = await f.read()
                    self.state = json.loads(content)
                logger.info(f"🧠 Memory loaded from {self.state_file}")
            except Exception as e:
                logger.error(f"❌ Failed to load memory: {e}")
        else:
            await self.save()

    async def save(self):
        """Save state to file"""
        os.makedirs(self.data_dir, exist_ok=True)
        try:
            async with aiofiles.open(self.state_file, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(self.state, indent=2, ensure_ascii=False))
        except Exception as e:
            logger.error(f"❌ Failed to save memory: {e}")

    async def ingest(self, text: str, source: str = "user"):
        """Ingest new information into the buffer and short-term layers"""
        now = datetime.now().isoformat()
        entry = {"text": text, "ts": now, "source": source}
        
        # Layer 1: Raw Buffer
        self.state["layers"]["raw_input_buffer"]["items"].append(entry)
        
        # Layer 2: Short Term
        self.state["layers"]["short_term"]["items"].append(entry)
        # Keep short term manageable (last 50 items)
        self.state["layers"]["short_term"]["items"] = self.state["layers"]["short_term"]["items"][-50:]
        
        # Layer 3: Working Context Update
        await self._update_working_context()
        
        await self.save()

    async def _update_working_context(self):
        """Heuristic update for working context"""
        # Take last 10 items from short_term as base context
        self.state["layers"]["working_context"]["items"] = self.state["layers"]["short_term"]["items"][-10:]

    async def get_layer(self, layer_name: str) -> Dict[str, Any]:
        """Get contents of a specific layer"""
        return self.state["layers"].get(layer_name, {})

    async def set_preference(self, key: str, value: Any):
        """Update preferences profile (Layer 6)"""
        self.state["layers"]["preferences_profile"][key] = value
        await self.save()

    async def add_task(self, task: str, priority: str = "NORMAL"):
        """Add task to tasks state (Layer 7)"""
        self.state["layers"]["tasks_state"]["items"].append({
            "task": task,
            "priority": priority,
            "ts": datetime.now().isoformat(),
            "status": "pending"
        })
        await self.save()
