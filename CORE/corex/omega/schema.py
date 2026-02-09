from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

class OmegaCommand(BaseModel):
    command: str
    target_llm: str = "dolphin"
    context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class OmegaResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    latency_ms: float
    shield_metrics: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PromptSnapshot(BaseModel):
    version: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime = Field(default_factory=datetime.utcnow)
