"""
DebateEngine — Multi-agent debate system for SZTAB.

Przebieg debaty (per topic):
1. Runda Analizy — każdy agent analizuje temat ze swojej perspektywy
2. Runda Rebuttal — każdy widzi propozycje innych, może poprzeć/zakwestionować
3. Głosowanie — każdy agent daje score 1-5 każdej propozycji
4. Konsensus — engine kompiluje top propozycje w action plan
"""
from __future__ import annotations

import json
import uuid
import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiohttp

from BUILDER.config import OLLAMA_URL, OLLAMA_TIMEOUT, ROUTING_TABLE, M_AI_SELF_DIR

logger = logging.getLogger("builder.debate")

# Agent definitions for SZTAB
SZTAB_AGENTS = {
    "STROZ_SECURITY": {
        "role": "Security Officer",
        "model": ROUTING_TABLE.get("security_audit", {}).get("model", "qwen3:8b"),
        "temperature": ROUTING_TABLE.get("security_audit", {}).get("temperature", 0.3),
        "perspective": "security, vulnerabilities, sandbox, input validation, OWASP",
    },
    "INZYNIER_PERF": {
        "role": "Performance Engineer",
        "model": ROUTING_TABLE.get("performance", {}).get("model", "qwen2.5-coder:7b"),
        "temperature": ROUTING_TABLE.get("performance", {}).get("temperature", 0.4),
        "perspective": "performance, caching, observability, cost tracking, latency",
    },
    "ARCHITEKT_UX": {
        "role": "UX & Frontend Architect",
        "model": ROUTING_TABLE.get("ux_design", {}).get("model", "qwen3:8b"),
        "temperature": ROUTING_TABLE.get("ux_design", {}).get("temperature", 0.5),
        "perspective": "frontend, UX, API integration, multi-modal, accessibility",
    },
    "TESTER_QA": {
        "role": "QA Commander",
        "model": ROUTING_TABLE.get("quality_assurance", {}).get("model", "qwen2.5-coder:7b"),
        "temperature": ROUTING_TABLE.get("quality_assurance", {}).get("temperature", 0.3),
        "perspective": "testing, coverage, regression, e2e, CI/CD",
    },
    "NAVIGATOR_RAG": {
        "role": "Knowledge & RAG Navigator",
        "model": ROUTING_TABLE.get("knowledge_rag", {}).get("model", "deepseek-r1:8b"),
        "temperature": ROUTING_TABLE.get("knowledge_rag", {}).get("temperature", 0.4),
        "perspective": "RAG pipeline, ChromaDB, embeddings, semantic search, knowledge management",
    },
    "KOWAL_TOOLS": {
        "role": "Tool Forge Master",
        "model": ROUTING_TABLE.get("tools_workflow", {}).get("model", "qwen2.5-coder:7b"),
        "temperature": ROUTING_TABLE.get("tools_workflow", {}).get("temperature", 0.4),
        "perspective": "tool registry, workflow/DAG engine, dynamic tools, automation",
    },
    "KRONIKARZ_DOCS": {
        "role": "Documentation Chronicler",
        "model": ROUTING_TABLE.get("documentation", {}).get("model", "phi4-mini"),
        "temperature": ROUTING_TABLE.get("documentation", {}).get("temperature", 0.5),
        "perspective": "documentation, prompt versioning, voice integration, changelog",
    },
}

# Default debate topics
DEFAULT_TOPICS = [
    "RAG Pipeline — ChromaDB jest zainstalowany ale nieużywany. Jak uruchomić pełny RAG?",
    "Security — Brak sandboxa, brak input validation na wielu endpointach. Co naprawić najpierw?",
    "Performance & Observability — Brak metryk, brak cost trackingu. Jak dodać monitoring?",
    "Frontend-API Integration — React frontend odłączony od API. Jak połączyć?",
    "Test Coverage — Tylko ~40% coverage. Strategia dojścia do 80%?",
    "Tool Registry — Tylko 6 narzędzi. Jakie nowe narzędzia są priorytetowe?",
    "Evolution Engine — Osierocony, nieużywany. Naprawić czy usunąć?",
]


@dataclass
class AgentResponse:
    agent_name: str
    role: str
    content: str
    model: str
    round_type: str  # "analysis" | "rebuttal" | "vote"
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metrics: dict = field(default_factory=dict)


@dataclass
class TopicResult:
    topic: str
    analyses: list[AgentResponse] = field(default_factory=list)
    rebuttals: list[AgentResponse] = field(default_factory=list)
    votes: dict = field(default_factory=dict)  # agent -> {proposal_agent: score}
    consensus: str = ""
    action_items: list[str] = field(default_factory=list)


@dataclass
class DebateSession:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    topics: list[str] = field(default_factory=list)
    results: list[TopicResult] = field(default_factory=list)
    status: str = "pending"  # pending | running | completed | failed
    started_at: str = ""
    completed_at: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "topics": self.topics,
            "status": self.status,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "topic_count": len(self.topics),
            "completed_topics": len(self.results),
            "error": self.error,
        }


class DebateEngine:
    def __init__(self, ollama_url: str | None = None, timeout: int | None = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.timeout = aiohttp.ClientTimeout(total=timeout or OLLAMA_TIMEOUT)
        self._sessions: dict[str, DebateSession] = {}

    def _build_context(self) -> str:
        """Build system context from real file state."""
        ctx_parts = []

        # Scan M-AI-SELF agents
        if M_AI_SELF_DIR.exists():
            agents = [d.name for d in M_AI_SELF_DIR.iterdir() if d.is_dir()]
            ctx_parts.append(f"Active agents in M-AI-SELF: {', '.join(agents)}")

        # Check key directories
        grota = M_AI_SELF_DIR.parent
        for name in ["BUILDER", "CORE", "DASHBOARD", "INBOX", "DATABASE"]:
            p = grota / name
            if p.exists():
                files = [f.name for f in p.rglob("*.py")][:10]
                ctx_parts.append(f"{name}/: {len(files)} Python files")

        # Check LUMEN CORE X
        core_x = Path("E:/[repo]")
        if core_x.exists():
            tests_dir = core_x / "tests"
            if tests_dir.exists():
                test_count = len(list(tests_dir.rglob("test_*.py")))
                ctx_parts.append(f"LUMEN CORE X tests: {test_count} test files")
            modules_dir = core_x / "modules"
            if modules_dir.exists():
                mod_count = len([d for d in modules_dir.iterdir() if d.is_dir()])
                ctx_parts.append(f"LUMEN CORE X modules: {mod_count}")

        return "\n".join(ctx_parts) if ctx_parts else "No context available."

    async def _call_ollama(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.5,
        system_prompt: str = "",
    ) -> tuple[str, dict]:
        """Call Ollama and return (response_text, metrics)."""
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 4096,
                "temperature": temperature,
                "num_predict": 1024,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.ollama_url}/api/generate", json=payload
                ) as resp:
                    if resp.status != 200:
                        return f"[ERROR: Ollama HTTP {resp.status}]", {}
                    data = await resp.json()
                    metrics = {
                        "eval_count": data.get("eval_count", 0),
                        "eval_duration_ms": (data.get("eval_duration", 0)) / 1e6,
                        "model": model,
                    }
                    return data.get("response", ""), metrics
        except Exception as e:
            logger.error(f"Ollama call failed ({model}): {e}")
            return f"[ERROR: {e}]", {}

    async def _run_analysis_round(
        self, topic: str, context: str, agents: dict
    ) -> list[AgentResponse]:
        """Round 1: Each agent analyzes the topic from their perspective."""
        responses = []

        for agent_name, cfg in agents.items():
            prompt = (
                f"## System Context\n{context}\n\n"
                f"## Topic for Analysis\n{topic}\n\n"
                f"As {cfg['role']} ({agent_name}), analyze this topic from your perspective "
                f"({cfg['perspective']}). Provide:\n"
                f"1. Your assessment of the current state\n"
                f"2. Top 3 concrete proposals with priority (HIGH/MEDIUM/LOW)\n"
                f"3. Estimated effort per proposal (hours/days)\n\n"
                f"Be specific and actionable. Max 300 words."
            )

            system_prompt = (
                f"You are {cfg['role']} in a multi-agent debate. "
                f"Your expertise: {cfg['perspective']}. "
                f"Be concise, specific, and actionable."
            )

            text, metrics = await self._call_ollama(
                prompt, cfg["model"], cfg["temperature"], system_prompt
            )

            responses.append(AgentResponse(
                agent_name=agent_name,
                role=cfg["role"],
                content=text,
                model=cfg["model"],
                round_type="analysis",
                metrics=metrics,
            ))
            logger.info(f"[Analysis] {agent_name} responded ({len(text)} chars)")

        return responses

    async def _run_rebuttal_round(
        self, topic: str, analyses: list[AgentResponse], agents: dict
    ) -> list[AgentResponse]:
        """Round 2: Each agent sees others' proposals and can support/challenge."""
        # Build summary of all analyses
        summary = "\n\n".join(
            f"### {a.agent_name} ({a.role}):\n{a.content}"
            for a in analyses
        )

        responses = []
        for agent_name, cfg in agents.items():
            prompt = (
                f"## Topic: {topic}\n\n"
                f"## All Proposals from Round 1:\n{summary}\n\n"
                f"As {cfg['role']} ({agent_name}), review ALL proposals above. "
                f"For each other agent's proposals:\n"
                f"- SUPPORT proposals that align with your expertise area\n"
                f"- CHALLENGE proposals that have gaps or risks\n"
                f"- SUGGEST improvements or combinations\n\n"
                f"Be constructive. Max 250 words."
            )

            system_prompt = (
                f"You are {cfg['role']} reviewing proposals from other specialists. "
                f"Be fair, constructive, and focus on your area: {cfg['perspective']}."
            )

            text, metrics = await self._call_ollama(
                prompt, cfg["model"], cfg["temperature"], system_prompt
            )

            responses.append(AgentResponse(
                agent_name=agent_name,
                role=cfg["role"],
                content=text,
                model=cfg["model"],
                round_type="rebuttal",
                metrics=metrics,
            ))
            logger.info(f"[Rebuttal] {agent_name} responded ({len(text)} chars)")

        return responses

    async def _run_voting_round(
        self, topic: str, analyses: list[AgentResponse], agents: dict
    ) -> dict[str, dict[str, int]]:
        """Round 3: Each agent scores proposals 1-5."""
        agent_names = [a.agent_name for a in analyses]
        votes: dict[str, dict[str, int]] = {}

        for agent_name, cfg in agents.items():
            proposals_text = "\n".join(
                f"- {a.agent_name}: {a.content[:200]}..."
                for a in analyses
            )

            other_agents = [n for n in agent_names if n != agent_name]
            vote_template = ", ".join(f'"{n}": <1-5>' for n in other_agents)
            prompt = (
                f"## Topic: {topic}\n\n"
                f"## Proposals:\n{proposals_text}\n\n"
                f"Rate each proposal from 1 (weak) to 5 (excellent). "
                f"You CANNOT vote for yourself. Respond in JSON format:\n"
                f'{{"votes": {{{vote_template}}}}}'
            )

            text, _ = await self._call_ollama(
                prompt, cfg["model"], cfg["temperature"],
                "Respond with valid JSON only. No explanation."
            )

            # Parse votes
            try:
                # Try to extract JSON from response
                text_clean = text.strip()
                if "{" in text_clean:
                    json_str = text_clean[text_clean.index("{"):text_clean.rindex("}") + 1]
                    parsed = json.loads(json_str)
                    vote_data = parsed.get("votes", parsed)
                    votes[agent_name] = {
                        k: max(1, min(5, int(v)))
                        for k, v in vote_data.items()
                        if k in agent_names and k != agent_name
                    }
                else:
                    votes[agent_name] = {}
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Vote parse failed for {agent_name}: {e}")
                votes[agent_name] = {}

            logger.info(f"[Vote] {agent_name}: {votes[agent_name]}")

        return votes

    def _compile_consensus(
        self,
        topic: str,
        analyses: list[AgentResponse],
        rebuttals: list[AgentResponse],
        votes: dict[str, dict[str, int]],
    ) -> tuple[str, list[str]]:
        """Compile votes into consensus and action items."""
        # Tally scores
        scores: dict[str, int] = {}
        for voter, vote_map in votes.items():
            for target, score in vote_map.items():
                scores[target] = scores.get(target, 0) + score

        # Rank by total score
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        # Build consensus
        lines = [f"## Consensus on: {topic}\n"]
        lines.append(f"**Ranking (by peer vote):**\n")
        for i, (agent, score) in enumerate(ranked, 1):
            analysis = next((a for a in analyses if a.agent_name == agent), None)
            preview = analysis.content[:150] + "..." if analysis else "N/A"
            lines.append(f"{i}. **{agent}** (score: {score}) — {preview}")

        # Extract action items from top 3
        action_items = []
        for agent, _ in ranked[:3]:
            analysis = next((a for a in analyses if a.agent_name == agent), None)
            if analysis:
                action_items.append(f"[{agent}] {analysis.content[:200]}")

        consensus = "\n".join(lines)
        return consensus, action_items

    async def run_debate(
        self,
        topics: list[str] | None = None,
        agents: dict | None = None,
    ) -> DebateSession:
        """Run a full debate session across all topics."""
        session = DebateSession(
            topics=topics or DEFAULT_TOPICS,
            status="running",
            started_at=datetime.utcnow().isoformat(),
        )
        self._sessions[session.id] = session

        context = self._build_context()
        debate_agents = agents or SZTAB_AGENTS

        logger.info(f"Debate {session.id} started: {len(session.topics)} topics, {len(debate_agents)} agents")

        try:
            for i, topic in enumerate(session.topics):
                logger.info(f"--- Topic {i+1}/{len(session.topics)}: {topic[:60]}...")

                # Round 1: Analysis
                analyses = await self._run_analysis_round(topic, context, debate_agents)

                # Round 2: Rebuttal
                rebuttals = await self._run_rebuttal_round(topic, analyses, debate_agents)

                # Round 3: Voting
                votes = await self._run_voting_round(topic, analyses, debate_agents)

                # Compile consensus
                consensus, action_items = self._compile_consensus(
                    topic, analyses, rebuttals, votes
                )

                result = TopicResult(
                    topic=topic,
                    analyses=analyses,
                    rebuttals=rebuttals,
                    votes=votes,
                    consensus=consensus,
                    action_items=action_items,
                )
                session.results.append(result)
                logger.info(f"Topic {i+1} completed. Action items: {len(action_items)}")

            session.status = "completed"
            session.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            logger.error(f"Debate {session.id} failed: {e}")
            session.status = "failed"
            session.error = str(e)

        return session

    def get_session(self, session_id: str) -> DebateSession | None:
        return self._sessions.get(session_id)

    def list_sessions(self) -> list[dict]:
        return [s.to_dict() for s in self._sessions.values()]

    def generate_report(self, session: DebateSession) -> str:
        """Generate full Markdown report of a debate."""
        lines = [
            f"# SZTAB DEBATE REPORT",
            f"**Session:** {session.id}",
            f"**Started:** {session.started_at}",
            f"**Completed:** {session.completed_at}",
            f"**Status:** {session.status}",
            f"**Topics:** {len(session.topics)}",
            f"**Agents:** {len(SZTAB_AGENTS)}",
            "",
            "---",
            "",
        ]

        for i, result in enumerate(session.results, 1):
            lines.append(f"## Topic {i}: {result.topic}")
            lines.append("")

            # Analyses
            lines.append("### Round 1: Analysis")
            for a in result.analyses:
                lines.append(f"\n#### {a.agent_name} ({a.role}) [{a.model}]")
                lines.append(a.content)

            # Rebuttals
            lines.append("\n### Round 2: Rebuttal")
            for r in result.rebuttals:
                lines.append(f"\n#### {r.agent_name} ({r.role})")
                lines.append(r.content)

            # Votes
            lines.append("\n### Round 3: Voting")
            for voter, vote_map in result.votes.items():
                vote_str = ", ".join(f"{k}: {v}/5" for k, v in vote_map.items())
                lines.append(f"- **{voter}**: {vote_str}")

            # Consensus
            lines.append(f"\n### Consensus")
            lines.append(result.consensus)

            # Action items
            if result.action_items:
                lines.append("\n### Action Items")
                for item in result.action_items:
                    lines.append(f"- {item}")

            lines.append("\n---\n")

        lines.append("\n## Summary")
        total_actions = sum(len(r.action_items) for r in session.results)
        lines.append(f"- **Topics debated:** {len(session.results)}")
        lines.append(f"- **Total action items:** {total_actions}")
        lines.append(f"\nAUUUUUUUUUUUUUUUUUUU!")

        return "\n".join(lines)
