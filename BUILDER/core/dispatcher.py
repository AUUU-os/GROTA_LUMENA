"""
Dispatcher — routes tasks to the best agent based on classification.
Reuses patterns from CORE/corex/swarm/smart_router.py.
"""

import re
import logging
from typing import Optional

from BUILDER.config import ROUTING_TABLE
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
]

FALLBACK_TYPE = "code_simple"


class Dispatcher:
    def classify(self, task: Task) -> str:
        """Classify task intent using keyword matching."""
        text = f"{task.title} {task.description}"
        scores: dict[str, int] = {}
        for task_type, pattern in _INTENT_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                scores[task_type] = len(matches)

        if not scores:
            return FALLBACK_TYPE

        return max(scores, key=scores.get)

    def select_route(self, task_type: str) -> dict:
        """Get routing config for a task type."""
        return ROUTING_TABLE.get(task_type, ROUTING_TABLE[FALLBACK_TYPE])

    def dispatch(self, task: Task) -> dict:
        """Classify task and return routing decision.

        Returns dict with: task_type, agent, bridge, model (optional).
        Does NOT execute — that's the bridge's job.
        """
        task_type = self.classify(task)
        route = self.select_route(task_type)

        task.task_type = task_type

        result = {
            "task_type": task_type,
            "agent": route["agent"],
            "bridge": route["bridge"],
        }

        if "model" in route:
            result["model"] = route["model"]
        if "temperature" in route:
            result["temperature"] = route["temperature"]
        if "system_prompt" in route:
            result["system_prompt"] = route["system_prompt"]

        logger.info(f"Dispatched task {task.id} ({task_type}) -> {route['agent']} via {route['bridge']}")
        return result

    def get_routing_table(self) -> dict:
        return dict(ROUTING_TABLE)
