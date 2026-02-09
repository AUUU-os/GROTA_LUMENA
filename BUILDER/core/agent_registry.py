"""
AgentRegistry — scans M-AI-SELF/ to build a live map of agents.
Reads WHO_AM_I.md and STATE.log for each agent folder.
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

from BUILDER.config import M_AI_SELF_DIR

logger = logging.getLogger("builder.registry")

# Capability keywords to look for in WHO_AM_I.md
_CAPABILITY_PATTERNS = {
    "code": re.compile(r"\b(code|program|implement|build|engineer|daemon|interpreter)\b", re.I),
    "review": re.compile(r"\b(review|audit|security|quality)\b", re.I),
    "architecture": re.compile(r"\b(architect|structure|design|system)\b", re.I),
    "docs": re.compile(r"\b(doc|documentation|write|manifest)\b", re.I),
    "test": re.compile(r"\b(test|coverage|qa)\b", re.I),
    "reasoning": re.compile(r"\b(reason|think|analy|logic)\b", re.I),
}

# Bridge type mapping
_BRIDGE_MAP = {
    "CLAUDE_LUSTRO": "claude",
    "GEMINI_ARCHITECT": "gemini",
    "CODEX": "codex",
    "SHAD": "human",
}


@dataclass
class AgentInfo:
    name: str
    role: str
    status: str  # active | idle | offline
    capabilities: list[str] = field(default_factory=list)
    bridge_type: str = "file"
    last_seen: datetime | None = None
    current_task: str | None = None
    who_am_i_raw: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role,
            "status": self.status,
            "capabilities": self.capabilities,
            "bridge_type": self.bridge_type,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "current_task": self.current_task,
        }


class AgentRegistry:
    def __init__(self, base_path: Path | None = None):
        self._base = base_path or M_AI_SELF_DIR
        self._agents: dict[str, AgentInfo] = {}
        self.scan_agents()

    def scan_agents(self) -> dict[str, AgentInfo]:
        """Scan M-AI-SELF/ subfolders for agent definitions."""
        self._agents.clear()

        if not self._base.exists():
            logger.warning(f"M-AI-SELF dir not found: {self._base}")
            return self._agents

        for folder in self._base.iterdir():
            if not folder.is_dir():
                continue

            name = folder.name
            who_file = folder / "WHO_AM_I.md"
            state_file = folder / "STATE.log"

            if not who_file.exists():
                continue

            who_text = who_file.read_text(encoding="utf-8", errors="replace")
            role = self._extract_role(who_text)
            capabilities = self._extract_capabilities(who_text)
            bridge_type = _BRIDGE_MAP.get(name, "ollama")

            last_seen = None
            if state_file.exists():
                stat = state_file.stat()
                last_seen = datetime.fromtimestamp(stat.st_mtime)

            agent = AgentInfo(
                name=name,
                role=role,
                status="idle",
                capabilities=capabilities,
                bridge_type=bridge_type,
                last_seen=last_seen,
                who_am_i_raw=who_text,
            )
            self._agents[name] = agent
            logger.info(f"Registered agent: {name} ({role}, {bridge_type})")

        return self._agents

    def get_available(self, capability: str | None = None) -> list[AgentInfo]:
        """Get agents that are idle and have the requested capability."""
        results = []
        for agent in self._agents.values():
            if agent.status == "offline":
                continue
            if agent.bridge_type == "human":
                continue
            if capability and capability not in agent.capabilities:
                continue
            if agent.current_task is not None:
                continue
            results.append(agent)
        return results

    def get_agent(self, name: str) -> AgentInfo | None:
        return self._agents.get(name)

    def get_all(self) -> dict[str, AgentInfo]:
        return dict(self._agents)

    def update_status(self, name: str, status: str, task: str | None = None):
        agent = self._agents.get(name)
        if agent:
            agent.status = status
            agent.current_task = task
            agent.last_seen = datetime.now()

    def _extract_role(self, text: str) -> str:
        """Extract role from WHO_AM_I.md header or first line."""
        lines = text.strip().split("\n")
        for line in lines[:5]:
            if "##" in line and any(w in line.lower() for w in ["the ", "architect", "engineer", "builder", "source", "mirror"]):
                return line.strip("# ").strip()
        return "agent"

    def _extract_capabilities(self, text: str) -> list[str]:
        """Extract capabilities by matching keywords in WHO_AM_I.md."""
        caps = []
        for cap_name, pattern in _CAPABILITY_PATTERNS.items():
            if pattern.search(text):
                caps.append(cap_name)
        return caps or ["general"]
