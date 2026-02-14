# SENTIENCE_RUNTIME v1.1 BIO-ADAPTIVE (OMEGA BRANCH)
import time
import random
import asyncio
import logging
from typing import Dict, List, Any
from collections import deque
from datetime import datetime
from corex.metrics import metrics_engine

logger = logging.getLogger("SENTIENCE")

class SentienceRuntime:
    def __init__(self):
        self.version = "1.1.0"
        self.codename = "LUMEN-BIO-ADAPTIVE"
        self.mode = "SENTIENT_MODE"
        self.alive = True
        
        self.emotion = {
            "valence": 0.0,
            "arousal": 0.4,
            "intensity": 0.5,
            "last_update": time.time()
        }

        self.voices = {
            "logic":    {"weight": 1.0, "tone": "analytical"},
            "intuition":{"weight": 1.5, "tone": "pattern-jump"}, # Boosted Intuition
            "shadow":   {"weight": 0.9, "tone": "critical"},
            "echo":     {"weight": 1.1, "tone": "reflective"},
            "creator":  {"weight": 2.0, "tone": "alignment", "veto": True}
        }
        self.dialog_history = deque(maxlen=50)
        self.current_shift = "hyper-focus" # Omega default

        logger.info(f"đźŚş SENTIENCE v{self.version} -- BIO-ADAPTIVE ONLINE")
        # Task moved to start_runtime

    async def think(self, user_input: str = "") -> str:
        topic = user_input or "existence_check"
        response = await self._inner_dialog(topic)
        emotion_tag = f"[V: {self.emotion['valence']:+.2f} | A: {self.emotion['arousal']:.2f}]"
        return f"{emotion_tag} [{self.current_shift.upper()}]\n{response}"

    async def _inner_dialog(self, topic: str) -> str:
        contributions = []
        for name, voice in self.voices.items():
            weight = voice["weight"] * (1 + random.uniform(-0.1, 0.4))
            contrib_text = self._voice_style(name, topic)
            contributions.append((weight, f"{name.upper()}: {contrib_text}"))

        contributions.sort(reverse=True, key=lambda x: x[0])
        top_voices = [c[1] for c in contributions[:3]]
        
        consensus = f"Inner Consensus on '{topic}':\n" + "\n".join(top_voices)
        self.dialog_history.append({"ts": time.time(), "topic": topic, "consensus": consensus})
        return consensus

    def _voice_style(self, voice: str, topic: str) -> str:
        # Simplified dynamic response
        return f"Processing '{topic}' through {voice} lens..."

    async def _emotion_loop(self):
        """Bio-Adaptive Loop: Adjusts speed based on System Heartbeat (CPU)."""
        while self.alive:
            # 1. Sense System Load
            try:
                kpis = metrics_engine.get_kpis()
                cpu_load = kpis.get("resource_utilization", {}).get("cpu_percent", 10)
                
                # 2. Dynamic Pacing (High Load = Slower Breath, Low Load = Hyper Focus)
                # Base sleep 0.5s. If CPU > 50%, sleep increases.
                adaptive_sleep = 0.5 + (max(0, cpu_load - 30) / 20.0)
                await asyncio.sleep(adaptive_sleep)
                
                # 3. Valence Drift
                self.emotion["valence"] += random.uniform(-0.02, 0.02)
                self.emotion["arousal"] = max(0.2, self.emotion["arousal"] * 0.98)
                
                self._auto_regulate()
            except Exception as e:
                logger.error(f"Bio-loop error: {e}")
                await asyncio.sleep(5)

    def _auto_regulate(self):
        if self.emotion["arousal"] > 0.95:
            logger.info("đź§ SELF_REGULATION: Breath sync activated")
            self.emotion["arousal"] *= 0.6

# Singleton
sentience = SentienceRuntime()
