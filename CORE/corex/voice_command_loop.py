"""
LUMEN VOICE COMMAND LOOP (Phase 11)
Integrates STT, Command Execution, and Alpha Voice Feedback.
"""

import threading
import time
import asyncio
import logging
import os
from corex.voice_input import VoiceListener
from corex.voice_output import get_voice_agent
from corex.audio_fx import audio_fx
from corex.sovereign_voice import sovereign_voice

logger = logging.getLogger(__name__)

class VoiceCommandLoop:
    """
    Handles the continuous cycle of listening, interpreting, and responding.
    """
    def __init__(self, daemon=None):
        self.daemon = daemon
        self.is_running = False
        self.thread = None
        self.last_log = "System wzbudzony."
        self.status = "idle"
        
        # Components
        self.listener = None
        self.voice_agent = None

    def start(self):
        if self.is_running: return
        self.is_running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        logger.info("🐺 VOICE COMMAND LOOP: STARTED")

    def stop(self):
        self.is_running = False
        self.status = "stopped"

    def _log(self, msg):
        self.last_log = msg
        print(f"🎤 [VOICE LOOP] {msg}")

    def _speak_alpha(self, text: str):
        """Responses are processed through the Alpha Wolf filter."""
        # Use sovereign_voice or voice_agent to generate raw, then apply FX
        raw_path = os.path.join("data", "voice_gen", "last_response_raw.wav")
        alpha_path = os.path.join("data", "voice_gen", "last_response_alpha.wav")
        
        # For now, we simulate the Alpha Bark for feedback
        # If we have a local voice engine, we'd use it here.
        # Fallback to standard speak if FX fails
        self.voice_agent.speak_sync(text)
        
    def _run(self):
        self.status = "initializing"
        
        # 1. Audio Input Capture & STT Init
        if not self.listener:
            self.listener = VoiceListener(model_name="small", energy_threshold=250)
        
        if not self.voice_agent:
            self.voice_agent = get_voice_agent()

        self._log("Wataha słucha. Powiedz 'LUMEN' lub daj rozkaz.")
        
        # Setup Async Loop for Daemon communication
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        while self.is_running:
            self.status = "listening"
            
            # 2. Capture & Process STT
            text = self.listener.listen(
                on_speaking=lambda: self._log("..."),
                on_transcribing=lambda: self._log("Analiza...")
            )

            if text and self.is_running:
                self._log(f"Zew: {text}")
                
                # 3. Command Parsing & Intent Recognition (via Daemon)
                if self.daemon:
                    try:
                        self.status = "executing"
                        result = loop.run_until_complete(self.daemon.execute_command(text))
                        
                        # 4. Action Execution Module (Handled by Daemon)
                        response_text = ""
                        if result["success"]:
                            response_text = "ZROBIONE. AUUUUU!"
                        else:
                            response_text = "BŁĄD RDZENIA. POWTÓRZ."

                        # 5. Feedback Loop (Auditory)
                        self._log(f"Odpowiedź: {response_text}")
                        self.voice_agent.speak_sync(response_text)
                        
                    except Exception as e:
                        self._log(f"Błąd pętli: {e}")
                else:
                    self._log("Brak połączenia z rdzeniem.")

            time.sleep(0.1)

# Singleton for the system
voice_loop = VoiceCommandLoop()
