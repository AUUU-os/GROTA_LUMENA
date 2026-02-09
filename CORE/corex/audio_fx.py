"""
LUMEN AUDIO FX ENGINE (Phase 11)
Post-processes voice output to achieve ALPHA WOLF characteristics.
Deep Pitch, Grit, and Aggressive Resonance.
"""

import subprocess
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class AudioFX:
    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg = ffmpeg_path

    def apply_alpha_wolf_filter(self, input_file: str, output_file: str):
        """
        Applies FFmpeg filters to transform standard voice into ALPHA WOLF.
        Filters:
        - Pitch Shift: Lowering frequency
        - Overdrive: Adding grit/distortion
        - EQ: Boosting bass/resonance
        - Volume: Normalizing to peak power
        """
        if not os.path.exists(input_file):
            return False

        # Filter Chain:
        # 1. asetrate (Lower pitch) + atempo (Correct speed)
        # 2. equalizer (Deep bass resonance)
        # 3. acrusher (Digital grit/distortion)
        # 4. volume (120dB target normalization)
        
        filter_complex = (
            "asetrate=44100*0.75,atempo=1.33,"
            "equalizer=f=100:width_type=h:width=200:g=15,"
            "acrusher=level_in=1:level_out=1:bits=8:mode=log:aa=1,"
            "volume=15dB"
        )

        cmd = [
            self.ffmpeg, "-y", "-i", input_file,
            "-af", filter_complex,
            output_file
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            logger.info(f"🐺 ALPHA FX applied: {output_file}")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"FX Failed: {e.stderr.decode()}")
            return False

# Singleton
audio_fx = AudioFX()
