"""
Pydantic schemas for Builder API.
Reuses patterns from CORE/corex/swarm/schemas.py.
"""

from enum import IntEnum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class TaskPriority(IntEnum):
    LOW = 0
    MEDIUM = 1
    HIGH = 2
    CRITICAL = 3


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    priority: str = Field("medium", pattern=r"^(low|medium|high|critical)$")
    assigned_to: Optional[str] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str  # pending | assigned | running | done | failed
    priority: str
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str
    result: Optional[str] = None
    error: Optional[str] = None
    task_type: Optional[str] = None


class DispatchRequest(BaseModel):
    agent: Optional[str] = None  # Force dispatch to specific agent
    bridge: Optional[str] = None  # Force specific bridge (ollama, claude, codex, gemini)
    model: Optional[str] = None  # Force specific Ollama model


class AgentResponse(BaseModel):
    name: str
    role: str
    status: str  # active | idle | offline
    capabilities: list[str]
    bridge_type: str
    last_seen: Optional[str] = None
    current_task: Optional[str] = None


class HealthResponse(BaseModel):
    builder: str  # "online"
    version: str
    ollama: str  # "online" | "offline"
    ollama_models: list[str]
    agents_total: int
    agents_active: int
    tasks_pending: int
    tasks_running: int
    uptime_seconds: float


class StatusResponse(BaseModel):
    status: str
    version: str
    uptime_seconds: float
    tasks: dict
    agents: dict


class WSEvent(BaseModel):
    type: str  # task_update | agent_status | system
    timestamp: str
    data: dict
