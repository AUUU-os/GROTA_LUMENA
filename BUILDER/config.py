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
OLLAMA_DEFAULT_MODEL = "qwen3:8b"

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
        "model": "qwen2.5-coder:7b",
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
        "model": "phi4-mini",
        "temperature": 0.5,
        "system_prompt": "Write clear, structured documentation.",
    },
    "test": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.3,
        "system_prompt": "Write comprehensive tests. Cover edge cases.",
    },
    "quick": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "phi4-mini",
        "temperature": 0.5,
        "system_prompt": "Answer briefly and directly.",
    },
    "reasoning": {
        "agent": "OLLAMA_WORKER",
        "bridge": "ollama",
        "model": "deepseek-r1:8b",
        "temperature": 0.4,
        "system_prompt": "Think step by step. Analyze carefully before answering.",
    },
    # === SZTAB AGENTÓW ===
    "security_audit": {
        "agent": "STROZ_SECURITY",
        "bridge": "ollama",
        "model": "qwen3:8b",
        "temperature": 0.3,
        "system_prompt": "You are a Security Officer. Analyze for vulnerabilities, injection risks, sandbox escapes, and OWASP Top 10. Be thorough and precise.",
    },
    "performance": {
        "agent": "INZYNIER_PERF",
        "bridge": "ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.4,
        "system_prompt": "You are a Performance Engineer. Analyze bottlenecks, suggest caching strategies, optimize latency, and track resource usage. Use metrics.",
    },
    "ux_design": {
        "agent": "ARCHITEKT_UX",
        "bridge": "ollama",
        "model": "qwen3:8b",
        "temperature": 0.5,
        "system_prompt": "You are a UX Architect. Design user experiences, plan frontend-API integration, ensure accessibility and multi-modal support.",
    },
    "quality_assurance": {
        "agent": "TESTER_QA",
        "bridge": "ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.3,
        "system_prompt": "You are a QA Commander. Write tests, find edge cases, ensure coverage, plan regression suites. Be systematic.",
    },
    "knowledge_rag": {
        "agent": "NAVIGATOR_RAG",
        "bridge": "ollama",
        "model": "deepseek-r1:8b",
        "temperature": 0.4,
        "system_prompt": "You are a Knowledge Navigator. Design RAG pipelines, manage embeddings, optimize retrieval, build semantic search. Think deeply.",
    },
    "tools_workflow": {
        "agent": "KOWAL_TOOLS",
        "bridge": "ollama",
        "model": "qwen2.5-coder:7b",
        "temperature": 0.4,
        "system_prompt": "You are a Tool Forge Master. Build tools, design workflows, create DAG pipelines, extend the tool registry. Write clean, working code.",
    },
    "documentation": {
        "agent": "KRONIKARZ_DOCS",
        "bridge": "ollama",
        "model": "phi4-mini",
        "temperature": 0.5,
        "system_prompt": "You are a Documentation Chronicler. Write clear docs, version prompts, maintain changelogs. Be structured and concise.",
    },
    "debate": {
        "agent": "SZTAB",
        "bridge": "ollama",
        "model": "qwen3:8b",
        "temperature": 0.5,
        "system_prompt": "Multi-agent debate orchestration.",
        "multi_agent": True,
    },
}

# === Version ===
VERSION = (BUILDER_DIR / "VERSION").read_text(encoding="utf-8").strip() if (BUILDER_DIR / "VERSION").exists() else "0.0.0"
