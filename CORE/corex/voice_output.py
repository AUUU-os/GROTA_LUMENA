"""
Voice Output Module
Text-to-Speech with ElevenLabs API (v2.x)
"""

import sys
import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path
import tempfile
from dotenv import load_dotenv

# Fix Windows encoding for emoji/unicode
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Try to import elevenlabs v2.x
try:
    from elevenlabs import play
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    print("⚠️  ElevenLabs v2.x not installed. Install with: pip install elevenlabs")

logger = logging.getLogger(__name__)

class VoiceAgent:
    """
    Voice output agent for CORE_X_AGENT using ElevenLabs v2.x
    """

    def __init__(
        self,
        voice_id: str = "EXAVITQu4vr4xnSDxMaL",  # LUMENA voice!
        model: str = "eleven_multilingual_v2",
        cache_dir: Optional[Path] = None
    ):
        self.voice_id = voice_id
        self.model = model
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / "corex_voice"
        self.cache_dir.mkdir(exist_ok=True)
        self.api_key = None
        self.client = None

        self._load_api_key()

        self.enabled = ELEVENLABS_AVAILABLE and self.api_key is not None
        if self.enabled:
            try:
                self.client = ElevenLabs(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize ElevenLabs client: {e}")
                self.enabled = False

    def _load_api_key(self):
        # Try .env in current dir
        load_dotenv()
        self.api_key = os.getenv("ELEVEN_API_KEY")

        # Fallback to Desktop/.env
        if not self.api_key:
            desktop_env = Path.home() / "Desktop" / ".env"
            if desktop_env.exists():
                load_dotenv(desktop_env)
                self.api_key = os.getenv("ELEVEN_API_KEY")

    async def speak(self, text: str, blocking: bool = True) -> bool:
        if not self.enabled:
            print(f"🔊 CORE_X: {text}")
            return False

        try:
            # Generate audio using v2 client - convert method
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model
            )
            
            # Convert generator to bytes
            audio_bytes = b"".join(audio_generator)

            # Play audio
            if blocking:
                play.play(audio_bytes)
            else:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, play.play, audio_bytes)
            return True

        except Exception as e:
            logger.error(f"Voice output error: {e}")
            print(f"🔊 CORE_X: {text}")
            return False

    def speak_sync(self, text: str) -> bool:
        if not self.enabled:
            print(f"🔊 CORE_X: {text}")
            return False

        try:
            audio_generator = self.client.text_to_speech.convert(
                text=text,
                voice_id=self.voice_id,
                model_id=self.model
            )
            audio_bytes = b"".join(audio_generator)
            play.play(audio_bytes)
            return True
        except Exception as e:
            logger.error(f"Voice output error: {e}")
            print(f"🔊 CORE_X: {text}")
            return False

    def get_available_voices(self) -> List[Any]:
        if not self.enabled: return []
        try:
            response = self.client.voices.get_all()
            return response.voices
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return []

    def set_voice(self, voice_id: str):
        """
        Change the voice ID

        Args:
            voice_id: New ElevenLabs voice ID
        """
        self.voice_id = voice_id

    def test(self):
        """Test voice output with sample message"""
        test_message = "AUUU! CORE_X_AGENT voice system online. I can speak now!"
        print(f"🎤 Testing voice output...")
        print(f"📝 Message: {test_message}")
        print(f"🎵 Voice ID: {self.voice_id}")
        print(f"🔧 Model: {self.model}")

        success = self.speak_sync(test_message)

        if success:
            print("✅ Voice test successful!")
        else:
            print("❌ Voice test failed (falling back to text)")

        return success


# Convenience functions for quick usage
_default_voice_agent: Optional[VoiceAgent] = None

def get_voice_agent() -> VoiceAgent:
    """Get or create default voice agent singleton"""
    global _default_voice_agent
    if _default_voice_agent is None:
        _default_voice_agent = VoiceAgent()
    return _default_voice_agent


async def speak(text: str, blocking: bool = True) -> bool:
    """
    Quick speak function using default voice agent

    Args:
        text: Text to speak
        blocking: If True, wait for audio to finish

    Returns:
        True if successful, False otherwise
    """
    agent = get_voice_agent()
    return await agent.speak(text, blocking)


def speak_sync(text: str) -> bool:
    """
    Quick synchronous speak function

    Args:
        text: Text to speak

    Returns:
        True if successful, False otherwise
    """
    agent = get_voice_agent()
    return agent.speak_sync(text)


# Example usage and test
if __name__ == "__main__":
    print("🎤 CORE_X_AGENT Voice Output Module\n")

    # Create voice agent
    voice = VoiceAgent()

    print(f"Voice enabled: {voice.enabled}")
    print(f"API key loaded: {voice.api_key is not None}")
    print()

    # Run test
    voice.test()

    print("\n🎯 Try different messages:")

    test_messages = [
        "Your working tree is clean. No changes detected.",
        "I found 3 commits in the log.",
        "Operation denied in TALK mode. Switch to DESIGN or EXEC mode to execute commands.",
    ]

    for i, msg in enumerate(test_messages, 1):
        print(f"\n{i}. {msg}")
        input("Press Enter to speak... ")
        voice.speak_sync(msg)

    print("\n✅ Voice output demo complete!")
