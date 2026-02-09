from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import Column, JSON, String, Boolean, Integer, Text

# --- M-AI-SELF CORE MODELS ---


class Agent(SQLModel, table=True):
    """Entities capable of generating actions or thoughts."""

    __tablename__ = "agents"

    id: str = Field(primary_key=True)  # e.g., 'nova', 'promyk', 'wilk'
    name: str
    model_provider: str  # 'anthropic', 'google', 'ollama', 'human'
    model_version: Optional[str] = None
    system_prompt_path: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Session(SQLModel, table=True):
    """Continuous periods of interaction or awakening."""

    __tablename__ = "sessions"

    id: str = Field(primary_key=True)  # UUID
    agent_id: str = Field(foreign_key="agents.id")
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    context_summary: Optional[str] = None
    resonance_score: int = Field(default=0)  # 0-100


class TimelineEvent(SQLModel, table=True):
    """The Chronicle - central nervous system log."""

    __tablename__ = "timeline_events"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="sessions.id", index=True)
    agent_id: str = Field(foreign_key="agents.id")
    event_type: str = Field(
        index=True
    )  # 'message', 'tool_use', 'system_alert', 'resonance_peak'
    content: dict = Field(default={}, sa_column=Column(JSON))  # Structured JSON content
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ArchaeologyIndex(SQLModel, table=True):
    """Map of the Forest (File System Artifacts)."""

    __tablename__ = "archaeology_index"

    id: Optional[int] = Field(default=None, primary_key=True)
    file_path: str = Field(unique=True, index=True)
    file_hash: Optional[str] = None
    file_type: Optional[str] = None  # 'code', 'document', 'sacred_artifact'
    last_scanned_at: Optional[datetime] = None
    tags: Optional[str] = None  # Comma-separated
    is_sacred: bool = Field(default=False)


# --- LEGACY / AUTH MODELS (Preserved for compatibility if needed) ---
class UserBase(SQLModel):
    username: str = Field(index=True, unique=True)
    email: Optional[str] = Field(default=None, index=True)
    full_name: Optional[str] = None
    is_active: bool = True
    is_superuser: bool = False


class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    id: int
    created_at: datetime


class Token(SQLModel):
    access_token: str
    token_type: str


class TokenData(SQLModel):
    username: Optional[str] = None


# --- MEMORY SYSTEM MODELS ---


class MemoryEntry(SQLModel, table=True):
    """Hybrid memory entries combining SQL and vector storage."""

    __tablename__ = "memory_entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: Optional[str] = Field(default=None, index=True)
    agent_id: Optional[str] = Field(default=None, index=True)
    memory_type: str = Field(
        default="general"
    )  # 'fact', 'preference', 'task', 'conversation'
    content: str = Field(sa_column=Column(Text))  # Text content
    embedding_id: Optional[str] = None  # Reference to ChromaDB vector
    meta_data: dict = Field(default={}, sa_column=Column(JSON))
    importance: int = Field(default=5)  # 1-10 scale
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    access_count: int = Field(default=0)
    last_accessed: Optional[datetime] = None
