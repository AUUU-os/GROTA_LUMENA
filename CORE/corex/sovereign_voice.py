"""
LUMEN SOVEREIGN VOICE (Phase 11)
Local, self-improving Text-to-Speech system.
Replaces ElevenLabs with high-fidelity cloning.
"""

import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

from .audio_fx import audio_fx

class SovereignVoice:
    """
    Autonomous local voice engine.
    Uses XTTS v2 for zero-shot cloning and potential fine-tuning.
    """
    def __init__(self, model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"):
        self.model_name = model_name
        self.device = "cpu" 
        self.reference_wav = r"E:\GEMINI\LUMEN\LUMEN_GLOS_20250701_222005.mp3"
        self.output_dir = Path("data/voice_gen")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tts = None 

    def speak(self, text: str, output_path: str = "output.wav", apply_fx: bool = True):
        """Generates speech and applies ALPHA FX."""
        temp_path = str(self.output_dir / "temp_raw.wav")
        final_path = output_path if output_path.endswith(".wav") else str(self.output_dir / output_path)

        if not self.tts:
            self.load_model()
        
        try:
            # 1. Generate Raw
            self.tts.tts_to_file(
                text=text,
                speaker_wav=self.reference_wav,
                language="pl",
                file_path=temp_path
            )
            
            # 2. Apply Alpha FX
            if apply_fx:
                success = audio_fx.apply_alpha_wolf_filter(temp_path, final_path)
                return final_path if success else temp_path
            
            return temp_path
        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            return None

    def learn_from_data(self, data_folder: str):
        """
        Placeholder for fine-tuning logic.
        Will scan folder for new voice samples and re-train the latent space.
        """
        print(f"🧬 SOVEREIGN VOICE: Analyzing new data in {data_folder}...")
        # Logic for auto-improvement goes here (Phase 11.2)
        return {"status": "evolution_queued", "new_samples": 0}

# Singleton
sovereign_voice = SovereignVoice()
