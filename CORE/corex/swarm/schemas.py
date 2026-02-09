from enum import IntEnum
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class TaskPriority(IntEnum):
    """Priorytet zadania w kolejce swarm."""

    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


class SwarmTask(BaseModel):
    """Payload for assigning a task to the Swarm."""

    intent: str = Field(..., description="What needs to be done?")
    model_preference: Optional[str] = Field(
        None, description="Specific model to use (e.g., dolphin-llama3)"
    )
    context: Optional[str] = Field(None, description="Additional context or memory")
    temperature: float = Field(0.7, ge=0.0, le=1.0)
    priority: TaskPriority = Field(
        TaskPriority.NORMAL,
        description="Task priority (0=LOW, 1=NORMAL, 2=HIGH, 3=CRITICAL)",
    )
    max_retries: int = Field(2, ge=0, le=5, description="Max retry attempts on failure")


class AgentResponse(BaseModel):
    """Standardized response from any Swarm Agent."""

    agent_name: str
    model_used: str
    content: str
    metadata: Dict[str, Any]
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RoutedTask(SwarmTask):
    """SwarmTask wzbogacony o informacje z Smart Routera."""

    routed_model: Optional[str] = Field(
        None, description="Model wybrany przez Smart Router"
    )
    system_prompt: Optional[str] = Field(
        None, description="System prompt z routing table"
    )
    task_type: Optional[str] = Field(
        None,
        description="Sklasyfikowany typ zadania (code/reasoning/analysis/creative/chat/quick)",
    )


class TaskResult(BaseModel):
    """Wynik wykonania zadania z historii."""

    task_intent: str
    task_type: str
    model_used: str
    priority: TaskPriority
    success: bool
    retries_used: int
    execution_time: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ModelHealthInfo(BaseModel):
    """Stan zdrowia pojedynczego modelu Ollama."""

    name: str
    available: bool
    size_gb: Optional[float] = None
    response_time_ms: Optional[float] = None
    routed_task_types: List[str] = Field(default_factory=list)


class SwarmHealthResponse(BaseModel):
    """Pelny health-check swarmu z per-model info."""

    ollama_online: bool
    models: List[ModelHealthInfo]
    total_models: int
    task_history_size: int
    queue_size: int


class SwarmStatus(BaseModel):
    """Health check for the Swarm."""

    active_agents: List[str]
    gpu_status: str
    queue_size: int
