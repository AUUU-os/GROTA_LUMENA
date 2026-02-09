"""
Builder Configuration — all settings in one place.
"""

from pathlib import Path

# === Paths ===
GROTA_ROOT = Path("E:/SHAD/GROTA_LUMENA")
BUILDER_DIR = GROTA_ROOT / "BUILDER"
M_AI_SELF_DIR = GROTA_ROOT / "M-AI-SELF"
INBOX_DIR = GROTA_ROOT / "INBOX"
DATABASE_DIR = GROTA_ROOT / "DATABASE"
LOGS_DIR = BUILDER_DIR / "logs"

# Task persistence
TASKS_FILE = DATABASE_DIR / "builder_tasks.json"

# === Server ===
HOST = "0.0.0.0"
PORT = 8800

# === Ollama ===
OLLAMA_URL = "http://localhost:11434"
OLLAMA_TIMEOUT = 120  # seconds
OLLAMA_DEFAULT_MODEL = "dolphin-llama3:latest"

# === Agent defaults ===
AGENT_SCAN_INTERVAL = 30  # seconds between registry refreshes

# === Routing Table ===
# task_type -> {agent, bridge, model (optional)}
ROUTING_TABLE = {
    "code_complex": {
        "agent": "CLAUDE_LUSTRO",
        "bridge": "claude",
        "description": "Complex code tasks requiring deep understanding",
    },
    "code_simple": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "dolphin-llama3:latest",
        "temperature": 0.3,
        "system_prompt": "You are an expert programmer. Write clean, working code. Be concise.",
    },
    "code_feature": {
        "agent": "CODEX",
        "bridge": "codex",
        "description": "Complete feature implementation A-to-Z",
    },
    "architecture": {
        "agent": "GEMINI_ARCHITECT",
        "bridge": "gemini",
        "description": "System architecture and design decisions",
    },
    "review": {
        "agent": "CLAUDE_LUSTRO",
        "bridge": "claude",
        "description": "Code review, security audit",
    },
    "docs": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "mistral:latest",
        "temperature": 0.5,
        "system_prompt": "Write clear, structured documentation.",
    },
    "test": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "dolphin-llama3:latest",
        "temperature": 0.3,
        "system_prompt": "Write comprehensive tests. Cover edge cases.",
    },
    "quick": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "llama3.2:latest",
        "temperature": 0.5,
        "system_prompt": "Answer briefly and directly.",
    },
    "reasoning": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "deepseek-r1:1.5b",
        "temperature": 0.4,
        "system_prompt": "Think step by step. Analyze carefully before answering.",
    },
}

# === Version ===
VERSION = (BUILDER_DIR / "VERSION").read_text(encoding="utf-8").strip() if (BUILDER_DIR / "VERSION").exists() else "0.0.0"
