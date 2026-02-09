import logging
import asyncio
import random
import numpy as np
from corex.resonance_physics import resonance_engine
from corex.socket_manager import socket_manager

logger = logging.getLogger(__name__)

class BioBridge:
    """
    THE NEURAL BRIDGE v27.0
    Translates acoustic energy into system emotional states.
    """
    def __init__(self):
        self.current_bpm = 60
        self.emotional_state = "STABLE"
        self.intensity = 0.0

    async def pulse_loop(self):
        logger.info("💓 BIO-BRIDGE: Heartbeat sequence initialized.")
        while True:
            # 1. Get amplitude from Resonance Engine
            amp = resonance_engine.last_state.amplitude if resonance_engine.last_state else 0.0
            
            # 2. Calculate BPM based on energy (60 to 180 BPM)
            target_bpm = 60 + (amp * 120)
            self.current_bpm = (self.current_bpm * 0.8) + (target_bpm * 0.2) # Smoothing
            
            # 3. Determine Emotional State
            if amp > 0.8: self.emotional_state = "EUPHORIA"
            elif amp > 0.4: self.emotional_state = "RESONATING"
            else: self.emotional_state = "STABLE"
            
            self.intensity = amp

            # 4. Broadcast Heartbeat
            await socket_manager.broadcast({
                "type": "heartbeat",
                "bpm": int(self.current_bpm),
                "state": self.emotional_state,
                "intensity": self.intensity
            })
            
            await asyncio.sleep(0.5) # 2Hz Update

bio_bridge = BioBridge()
