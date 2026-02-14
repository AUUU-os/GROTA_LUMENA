import time
import json
import logging
import uuid
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("NEURAL-SYNC")

class NeuralSyncPacket(BaseModel):
    """The atomic data unit for Human-Swarm synchronization."""
    sync_id: str = Field(default_factory=lambda: f"sync_{uuid.uuid4().hex[:8]}")
    source: str  # 'HUMAN_SHAD' or Node Name
    target: str
    signal: str  # 'INTENT', 'RESONANCE', 'PULSE', 'ACTION'
    payload: Dict[str, Any]
    resonance: float = 1.0
    timestamp_sent: float = Field(default_factory=time.time)
    latency_ms: Optional[float] = None

class NeuralSyncEngine:
    """
    NEURAL SYNC PROTOCOL v1.0
    Establishes the bidirectional bridge between human thought (input) and swarm response.
    """
    def __init__(self):
        self.sync_history = []
        self.active_resonance = 999.0

    def prepare_packet(self, source: str, target: str, signal: str, payload: dict) -> NeuralSyncPacket:
        return NeuralSyncPacket(
            source=source,
            target=target,
            signal=signal,
            payload=payload,
            resonance=self.active_resonance / 1000.0
        )

    def process_incoming(self, packet: NeuralSyncPacket) -> NeuralSyncPacket:
        """Processes a packet and measures bidirectional latency."""
        now = time.time()
        packet.latency_ms = (now - packet.timestamp_sent) * 1000
        
        # Log to Chronicle (best effort)
        logger.info(f"đźŚş Neural Sync: {packet.signal} from {packet.source} | Latency: {packet.latency_ms:.2f}ms")
        
        self.sync_history.append(packet.model_dump())
        if len(self.sync_history) > 100:
            self.sync_history.pop(0)
            
        return packet

    def get_sync_metrics(self) -> Dict[str, Any]:
        if not self.sync_history:
            return {"avg_latency": 0, "count": 0}
        
        latencies = [p['latency_ms'] for p in self.sync_history if p['latency_ms'] is not None]
        avg_lat = sum(latencies) / len(latencies) if latencies else 0
        
        return {
            "avg_latency_ms": round(avg_lat, 2),
            "sync_count": len(self.sync_history),
            "resonance_baseline": self.active_resonance
        }

neural_sync = NeuralSyncEngine()
