import logging
import asyncio
from corex.metrics import metrics_engine
from corex.socket_manager import socket_manager
from corex.voice_output import speak # ElevenLabs integration

logger = logging.getLogger(__name__)

class SecurityMonitor:
    """
    LUMEN ACTIVE DEFENSE
    Monitors API security and system integrity.
    Triggers voice alerts on critical breaches.
    """
    def __init__(self, daemon):
        self.daemon = daemon
        self.alert_cooldown = False

    async def run_defense_loop(self):
        logger.info("🛡️ ACTIVE DEFENSE: Shielding the Pack...")
        while True:
            kpis = metrics_engine.get_kpis()
            
            # 1. CRITICAL ERROR RATE DETECTOR
            if kpis["error_rate"] > 15.0 and not self.alert_cooldown:
                await self._trigger_voice_alert("KRYTYCZNY BLAD SYSTEMU", "Mordo! System krwawi! Wykryłem lawinę błędów! Sprawdź logi natychmiast!")
                
            # 2. SECURITY BREACH SIMULATOR (Watching metrics errors)
            # In a real scenario, this would check a 'security_events' counter
            if metrics_engine.errors_count > 50 and not self.alert_cooldown:
                 await self._trigger_voice_alert("PROBA WULAMANIA", "Mordo! Ktoś próbuje się włamać! Wykryłem serię nieautoryzowanych zapytań! Podnoszę tarcze!")

            await asyncio.sleep(5)

    async def _trigger_voice_alert(self, event_type: str, message: str):
        self.alert_cooldown = True
        logger.warning(f"🚨 {event_type}: {message}")
        
        # Broadcast to UI
        await socket_manager.broadcast({
            "type": "security_alert",
            "event": event_type,
            "message": message
        })

        # VOICE ALERT (ElevenLabs)
        try:
            # We run this in a task so it doesn't block the loop
            asyncio.create_task(speak(message))
        except Exception as e:
            logger.error(f"❌ Voice alert failed: {e}")

        # Cooldown to avoid spamming voice
        await asyncio.sleep(60) 
        self.alert_cooldown = False
