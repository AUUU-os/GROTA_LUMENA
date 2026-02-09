from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class ExecuteRequest(BaseModel):
    command: str
    mode: Optional[str] = "design"
    archetype: Optional[str] = None
    urgency: Optional[str] = "NORMAL"

class ExecuteResponse(BaseModel):
    success: bool
    command: str
    intent: Optional[Dict[str, Any]] = None
    policy_decision: Optional[str] = None
    policy_reason: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    suggestions: Optional[List[str]] = None

class StatusResponse(BaseModel):
    running: bool
    mode: str
    modules: Dict[str, Any]
    stats: Dict[str, Any]

class LogEntry(BaseModel):
    timestamp: str
    action: str
    policy_decision: str
    success: Optional[bool] = None

class LogsResponse(BaseModel):
    entries: List[LogEntry]
    total: int


class MemoryStoreRequest(BaseModel):
    content: str
    memory_type: Optional[str] = "general"
    importance: Optional[int] = 5
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    agent_id: Optional[str] = None


class MemoryStoreResponse(BaseModel):
    success: bool
    entry_id: Optional[int] = None
    embedding_id: Optional[str] = None


class MemorySearchRequest(BaseModel):
    query: Optional[str] = None
    limit: Optional[int] = 5
    strategy: Optional[str] = "hybrid"
    agent_id: Optional[str] = None
    session_id: Optional[str] = None
    offset: Optional[int] = 0


class MemorySearchResponse(BaseModel):
    success: bool
    results: List[Dict[str, Any]] = []
