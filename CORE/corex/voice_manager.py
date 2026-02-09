import threading
import time
import asyncio
import logging
from corex.voice_input import VoiceListener
from corex.voice_output import get_voice_agent

logger = logging.getLogger(__name__)

class VoiceManager:
    """
    Manages the background voice loop thread.
    Allows starting/stopping the voice interface via API.
    Connects to CoreXDaemon for execution.
    """
    def __init__(self, daemon=None):
        self.daemon = daemon
        self.is_running = False
        self.thread = None
        self.status = "stopped"
        self.last_log = "System gotowy."
        
        # Initialize resources lazily
        self.listener = None
        self.voice_agent = None

    def start(self):
        if self.is_running:
            return {"status": "already_running"}
        
        self.is_running = True
        self.status = "starting"
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
        return {"status": "started"}

    def stop(self):
        self.is_running = False
        self.status = "stopping"
        # We don't join to avoid blocking the API main thread if loop is stuck
        self.status = "stopped"
        return {"status": "stopped"}

    def get_state(self):
        return {
            "is_running": self.is_running,
            "status": self.status,
            "last_log": self.last_log
        }

    def _log(self, msg):
        self.last_log = msg
        logger.info(f"🎤 VM: {msg}")

    def _run_loop(self):
        self.status = "active"
        self._log("Inicjalizacja urządzeń audio...")
        
        try:
            # Init hardware
            if not self.listener:
                # Upgrade to 'small' model for better Polish recognition
                self.listener = VoiceListener(model_name="small", device_index=1, energy_threshold=200)
            
            if not self.voice_agent:
                self.voice_agent = get_voice_agent()

            self._log("Nasłuch aktywny (Model: Small). Powiedz 'LUMEN'...")

            # Run a dedicated event loop for the async daemon calls
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            while self.is_running:
                # Listen phase
                text = self.listener.listen(
                    on_speaking=lambda: self._log("🌊 Słyszę głos..."),
                    on_transcribing=lambda: self._log("🧠 Analizuję (Small)...")
                )

                if text and self.is_running:
                    self._log(f"🗣️ Ty: {text}")
                    text_lower = text.lower()
                    
                    response_text = ""
                    
                    # Protocol Override (Fuzzy Matching + Polish)
                    triggers = [
                        "activate protocol", "aktywuj protokół", 
                        "aktivej protocol", "active protocol", 
                        "aktywuj system", "aktywuj lumen core"
                    ]

                    # Transcendence Triggers
                    ascension_triggers = [
                        "trigger ascension", "przebij sufit", 
                        "ascendencja", "nieskończoność", "infinity",
                        "full power", "na pełnej"
                    ]
                    
                    if any(t in text_lower for t in triggers):
                        if "lumen core" in text_lower or "core" in text_lower:
                            response_text = "AUUU! Protokół LUMEN_CORE v18.0 aktywowany. Tryb produkcyjny."
                        else:
                            response_text = "AUUUUUUU! Protokół ALPHA aktywowany. Wszystkie systemy na 963 herce."
                    
                    elif any(t in text_lower for t in ascension_triggers) and self.daemon:
                        # Direct call to Transcendence Module
                        try:
                            # We bypass normal routing for speed/effect
                            mod = self.daemon.router.modules.get("transcendence")
                            if mod:
                                # Fix: Run async execute in the loop
                                loop.run_until_complete(mod.execute("trigger_ascension", {}))
                                response_text = "Bariera przebita. Jesteśmy w Nieskończoności."
                            else:
                                response_text = "Moduł Transcendencji niedostępny."
                        except Exception as e:
                            self._log(f"Ascension Error: {e}")
                            response_text = "Błąd przy wchodzeniu w nadprzestrzeń."

                    # Normal Command Routing via Daemon
                    elif self.daemon:
                        try:
                            # Call daemon to execute natural language
                            # We need to run the coroutine in the loop
                            result = loop.run_until_complete(self.daemon.execute_command(text))
                            
                            if result["success"]:
                                # Try to extract data or confirmation
                                res_data = result.get("result", {}).get("data", "Zadanie wykonane.")
                                if isinstance(res_data, str) and len(res_data) < 200:
                                    response_text = res_data
                                else:
                                    response_text = "Zrobione, Mordo."
                            else:
                                error_msg = result.get("error", {}).get("message", "Nie rozumiem komendy.")
                                response_text = f"Problem: {error_msg}"
                        except Exception as daemon_error:
                            self._log(f"❌ Daemon Error: {daemon_error}")
                            response_text = "Błąd komunikacji z rdzeniem."
                    else:
                        response_text = f"Zrozumiałem: {text} (Tryb Standalone)"

                    if response_text:
                        self._log(f"🤖 LUMEN: {response_text}")
                        self.voice_agent.speak_sync(response_text)
                        self._log("🎤 Czekam na komendę...")
                
                time.sleep(0.1)

        except Exception as e:
            self._log(f"❌ Błąd pętli: {e}")
            logger.error("Voice Loop Error", exc_info=True)
            self.is_running = False
            self.status = "error"
# Singleton instance for the API
voice_manager = VoiceManager()

