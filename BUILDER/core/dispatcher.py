from __future__ import annotations

"""
Dispatcher — routes tasks to the best agent based on classification.
Reuses patterns from CORE/corex/swarm/smart_router.py.
"""

import re
import json
import logging
from typing import Optional

import aiohttp

from BUILDER.config import OLLAMA_URL, ROUTING_TABLE
from BUILDER.core.task_manager import Task

logger = logging.getLogger("builder.dispatcher")

# Intent classification patterns (from smart_router.py, extended for Builder)
_INTENT_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("code_complex", re.compile(
        r"\b(refactor|security|audit|complex|architect|critical|bug.*fix|deep.*review)\b", re.I
    )),
    ("code_feature", re.compile(
        r"\b(feature|endpoint.*logic.*test|full.*implementation|A.*to.*Z|from.*scratch)\b", re.I
    )),
    ("code_simple", re.compile(
        r"\b(code|implement|function|class|script|debug|fix|program|write.*code|python|javascript|html|css|sql|api)\b", re.I
    )),
    ("architecture", re.compile(
        r"\b(architect|design|structure|system.*design|plan|blueprint|schema)\b", re.I
    )),
    ("review", re.compile(
        r"\b(review|check|verify|validate|inspect|assess)\b", re.I
    )),
    ("reasoning", re.compile(
        r"\b(why|explain|reason|logic|proof|think.*step|math|calculate|solve)\b", re.I
    )),
    ("docs", re.compile(
        r"\b(doc|documentation|readme|comment|describe|write.*doc)\b", re.I
    )),
    ("test", re.compile(
        r"\b(test|unittest|pytest|coverage|spec|assert)\b", re.I
    )),
    ("quick", re.compile(
        r"\b(yes or no|true or false|translate|define|what is|short|tldr|quick)\b", re.I
    )),
    # === SZTAB AGENTÓW ===
    ("security_audit", re.compile(
        r"\b(security.*audit|vulnerability|sandbox|OWASP|injection|XSS|CSRF|penetration|exploit|CVE)\b", re.I
    )),
    ("performance", re.compile(
        r"\b(performance|latency|throughput|cache.*strateg|profil|bottleneck|optimi.*speed|observability|metric.*track)\b", re.I
    )),
    ("ux_design", re.compile(
        r"\b(UX|user.*experience|frontend.*design|interface|accessibility|responsive|multi.*modal.*UI)\b", re.I
    )),
    ("quality_assurance", re.compile(
        r"\b(QA|quality.*assurance|regression.*test|e2e.*test|test.*plan|coverage.*target|CI.*CD.*pipeline)\b", re.I
    )),
    ("knowledge_rag", re.compile(
        r"\b(RAG|retrieval.*augment|embedding|vector.*store|ChromaDB|semantic.*search|knowledge.*base)\b", re.I
    )),
    ("tools_workflow", re.compile(
        r"\b(tool.*registry|workflow.*engine|DAG|pipeline.*build|dynamic.*tool|automat.*chain)\b", re.I
    )),
    ("documentation", re.compile(
        r"\b(documentation.*system|prompt.*version|changelog.*maintain|API.*doc|voice.*integrat)\b", re.I
    )),
    ("debate", re.compile(
        r"\b(debate|debata|multi.*agent.*discuss|sztab|consensus|panel.*dyskus)\b", re.I
    )),
]

FALLBACK_TYPE = "code_simple"

_VALID_TYPES = frozenset(t for t, _ in _INTENT_PATTERNS)


class Dispatcher:
    def __init__(self, registry=None):
        self._registry = registry
        self._needs_ollama: bool = False

    def classify(self, task: Task) -> str:
        """Classify task intent using keyword matching."""
        text = f"{task.title} {task.description}"
        scores: dict[str, int] = {}
        for task_type, pattern in _INTENT_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                scores[task_type] = len(matches)

        if not scores:
            result = FALLBACK_TYPE
        else:
            result = max(scores, key=scores.get)

        # Flag for async caller: if keyword matching fell back AND the task
        # text is non-trivial, Ollama classification may yield a better result.
        combined_len = len(task.title or "") + len(task.description or "")
        if result == FALLBACK_TYPE and combined_len > 20:
            self._needs_ollama = True
        else:
            self._needs_ollama = False

        return result


    async def classify_with_ollama(self, task: Task) -> str:
        """Classify task intent via Ollama LLM as fallback.

        Calls localhost Ollama with llama3.2:latest, asks it to pick one of
        the known task types.  Returns the type string or falls back to
        keyword-based classification on any error.
        """
        prompt = (
            "You are a task classifier. Given a task title and description, "
            "respond with EXACTLY ONE of the following types and nothing else:\n"
            "code_complex, code_simple, code_feature, architecture, review, "
            "reasoning, docs, test, quick, security_audit, performance, "
            "ux_design, quality_assurance, knowledge_rag, tools_workflow, "
            "documentation, debate\n\n"
            f"Title: {task.title}\n"
            f"Description: {task.description}\n\n"
            "Type:"
        )

        url = f"{OLLAMA_URL}/api/generate"
        payload = {
            "model": "phi4-mini",
            "prompt": prompt,
            "stream": False,
        }

        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url, json=payload) as resp:
                    if resp.status != 200:
                        logger.warning(
                            "Ollama classification failed with status %s, "
                            "falling back to keyword", resp.status,
                        )
                        return self.classify(task)

                    data = await resp.json()
                    raw = data.get("response", "").strip().lower()

                    # Extract the first valid type from the response
                    for valid_type in _VALID_TYPES:
                        if valid_type in raw:
                            logger.info(
                                "Ollama classified task %s as '%s'",
                                task.id, valid_type,
                            )
                            return valid_type

                    logger.warning(
                        "Ollama returned unrecognised type '%s', "
                        "falling back to keyword", raw,
                    )
                    return self.classify(task)

        except Exception as exc:
            logger.warning(
                "Ollama classification error: %s, falling back to keyword", exc,
            )
            return self.classify(task)

    async def classify_async(self, task: Task) -> str:
        """Classify task, using Ollama as fallback when keywords are ambiguous.

        Runs keyword-based classify() first.  If the result was a fallback
        AND the task text is long enough to be worth a second opinion, calls
        classify_with_ollama().
        """
        keyword_result = self.classify(task)
        if self._needs_ollama:
            return await self.classify_with_ollama(task)
        return keyword_result

    def select_route(self, task_type: str) -> dict:
        """Get routing config for a task type."""
        return ROUTING_TABLE.get(task_type, ROUTING_TABLE[FALLBACK_TYPE])

    def check_availability(self, agent_name: str) -> bool:
        """Check if an agent is available (not offline, no current task).

        If no registry is set, always returns True.
        """
        if self._registry is None:
            return True

        agent = self._registry.get_agent(agent_name)
        if agent is None:
            return True

        if agent.status == "offline":
            return False
        if agent.current_task is not None:
            return False

        return True

    def find_alternative(self, task_type: str) -> dict | None:
        """Find an alternative agent when the primary one is busy.

        For any task_type, if the primary agent is busy, check if
        OLLAMA_WORKER is available (ollama can do anything).
        Returns the alternative route dict, or None if nobody available.
        """
        if self._registry is None:
            return None

        # Check if OLLAMA_WORKER is available as universal fallback
        if self.check_availability("OLLAMA_WORKER"):
            fallback_route = dict(ROUTING_TABLE.get(FALLBACK_TYPE, {}))
            fallback_route["agent"] = "OLLAMA_WORKER"
            fallback_route["bridge"] = "ollama"
            return fallback_route

        return None

    def dispatch(self, task: Task) -> dict:
        """Classify task and return routing decision.

        Returns dict with: task_type, agent, bridge, model (optional),
        confidence, and fallback (if alternative was used).
        Does NOT execute — that is the bridge's job.
        """
        task_type = self.classify(task)
        route = self.select_route(task_type)

        task.task_type = task_type

        # Calculate confidence based on keyword matches
        text = f"{task.title} {task.description}"
        is_fallback = (task_type == FALLBACK_TYPE)
        match_count = 0
        for tt, pattern in _INTENT_PATTERNS:
            if tt == task_type:
                matches = pattern.findall(text)
                match_count = len(matches)
                break

        if is_fallback and match_count == 0:
            confidence = 0.5
        elif match_count >= 3:
            confidence = 1.0
        else:
            confidence = 0.7

        # Check availability if registry is set
        fallback_used = False
        if self._registry is not None:
            agent_name = route["agent"]
            if not self.check_availability(agent_name):
                alternative = self.find_alternative(task_type)
                if alternative is not None:
                    route = alternative
                    fallback_used = True
                    logger.info(
                        f"Primary agent {agent_name} busy for task {task.id}, "
                        f"falling back to {route['agent']}"
                    )

        result = {
            "task_type": task_type,
            "agent": route["agent"],
            "bridge": route["bridge"],
            "confidence": confidence,
        }

        if fallback_used:
            result["fallback"] = True

        if "model" in route:
            result["model"] = route["model"]
        if "temperature" in route:
            result["temperature"] = route["temperature"]
        if "system_prompt" in route:
            result["system_prompt"] = route["system_prompt"]

        logger.info(f"Dispatched task {task.id} ({task_type}) -> {route['agent']} via {route['bridge']} [confidence={confidence}]")
        return result

    def get_routing_table(self) -> dict:
        return dict(ROUTING_TABLE)
