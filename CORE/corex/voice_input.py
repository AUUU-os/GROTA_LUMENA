"""
Voice Input Module
Speech-to-Text with Faster-Whisper
"""

import sys
import os
import wave
import time
import numpy as np
from typing import Optional, Callable, List
from pathlib import Path
import tempfile
import threading

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Try to import audio libraries
try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    print("⚠️  sounddevice not installed. Install with: pip install sounddevice")

try:
    from faster_whisper import WhisperModel
    FASTER_WHISPER_AVAILABLE = True
except ImportError:
    FASTER_WHISPER_AVAILABLE = False
    print("⚠️  faster-whisper not installed. Install with: pip install faster-whisper")


class VoiceListener:
    """
    Voice input listener using Faster-Whisper
    """

    def __init__(
        self,
        model_name: str = "small",
        sample_rate: int = 16000,
        chunk_duration: float = 0.5,
        energy_threshold: int = 300,
        silence_duration: float = 1.5,
        max_recording_duration: float = 10.0,
        device_index: Optional[int] = None
    ):
        self.model_name = model_name
        self.sample_rate = sample_rate
        self.chunk_duration = chunk_duration
        self.chunk_size = int(sample_rate * chunk_duration)
        self.energy_threshold = energy_threshold
        self.silence_duration = silence_duration
        self.max_recording_duration = max_recording_duration
        self.device_index = device_index

        # Check availability
        self.enabled = FASTER_WHISPER_AVAILABLE and SOUNDDEVICE_AVAILABLE

        if not self.enabled:
            return

        # Load Faster-Whisper model
        print(f"📥 Loading Faster-Whisper '{model_name}' on CPU...")
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
        print(f"✅ Faster-Whisper model loaded!")

        self.audio_buffer = []
        self.is_recording = False

    def get_audio_energy(self, audio_chunk: np.ndarray) -> float:
        return np.sqrt(np.mean(audio_chunk**2))

    def record_audio(
        self,
        on_start: Optional[Callable] = None,
        on_speaking: Optional[Callable] = None,
        on_silence: Optional[Callable] = None
    ) -> Optional[np.ndarray]:
        if not self.enabled:
            return None

        self.audio_buffer = []
        self.is_recording = True
        silence_chunks = 0
        max_silence_chunks = int(self.silence_duration / self.chunk_duration)
        max_chunks = int(self.max_recording_duration / self.chunk_duration)
        speaking_started = False

        if on_start:
            on_start()

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype='int16',
                device=self.device_index
            ) as stream:
                chunk_count = 0

                while self.is_recording and chunk_count < max_chunks:
                    audio_chunk, _ = stream.read(self.chunk_size)
                    audio_chunk = audio_chunk.flatten()
                    energy = self.get_audio_energy(audio_chunk.astype(np.float32))

                    if energy > self.energy_threshold:
                        if not speaking_started:
                            speaking_started = True
                            if on_speaking: on_speaking()
                        self.audio_buffer.append(audio_chunk)
                        silence_chunks = 0
                    else:
                        if speaking_started:
                            self.audio_buffer.append(audio_chunk)
                            silence_chunks += 1
                            if silence_chunks >= max_silence_chunks:
                                if on_silence: on_silence()
                                break
                    chunk_count += 1

            if self.audio_buffer:
                return np.concatenate(self.audio_buffer)
            return None

        except Exception as e:
            print(f"❌ Recording error: {e}")
            return None

    def transcribe(self, audio_data: np.ndarray) -> Optional[str]:
        if not self.enabled or audio_data is None:
            return None

        try:
            audio_float = audio_data.astype(np.float32) / 32768.0
            audio_float = np.clip(audio_float * 5.0, -1.0, 1.0)

            segments, info = self.model.transcribe(audio_float, language="pl", beam_size=5)
            text = " ".join([s.text for s in segments]).strip()
            print(f"DEBUG Faster-Whisper text: '{text}'")
            return text if text else None

        except Exception as e:
            print(f"❌ Faster-Whisper error: {e}")
            return None

    def listen(self, on_start=None, on_speaking=None, on_silence=None, on_transcribing=None):
        if not self.enabled: return None
        audio_data = self.record_audio(on_start, on_speaking, on_silence)
        if audio_data is None: return None
        if on_transcribing: on_transcribing()
        return self.transcribe(audio_data)

    def stop(self):
        self.is_recording = False

class WakeWordDetector:
    def __init__(self, wake_words: Optional[List[str]] = None):
        self.wake_words = wake_words or [
            "lumen", "hey lumen", "auuu", "auu", 
            "mordo", "mordeczko", "mordeczko kochana", "mordeczko moja",
            "mordeczka", "mordunio"
        ]

    def detect(self, text: str) -> tuple[bool, Optional[str]]:
        if not text: return False, None
        text_lower = text.lower().strip()
        for wake_word in self.wake_words:
            if wake_word in text_lower:
                parts = text_lower.split(wake_word, 1)
                remaining = parts[1].strip() if len(parts) > 1 else None
                return True, remaining
        return False, None

class VoiceInputAgent:
    def __init__(self, model_name: str = "small", device_index: Optional[int] = 1):
        self.listener = VoiceListener(model_name=model_name, device_index=device_index)
        self.wake_detector = WakeWordDetector()
        self.enabled = self.listener.enabled

    def wait_for_command(self) -> Optional[str]:
        if not self.enabled: return None
        while True:
            text = self.listener.listen(
                on_start=lambda: print("🎤 Listening..."),
                on_speaking=lambda: print("🔊 Voice detected..."),
                on_transcribing=lambda: print("🧠 Transcribing...")
            )
            if text:
                detected, remaining = self.wake_detector.detect(text)
                if detected:
                    return remaining if remaining else self.listen_for_command()
        return None

    def listen_for_command(self) -> Optional[str]:
        return self.listener.listen(on_speaking=lambda: print("🔊 Recording command..."))

# Convenience singleton
_default_voice_input = None
def get_voice_input() -> VoiceInputAgent:
    global _default_voice_input
    if _default_voice_input is None:
        _default_voice_input = VoiceInputAgent()
    return _default_voice_input