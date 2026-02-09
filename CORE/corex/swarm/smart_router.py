"""
Smart Router for Ollama Swarm — automatyczny dobor modelu do typu zadania.
"""

import re
from typing import Dict, List, Optional
from .schemas import SwarmTask


# Routing table: task_type -> {model, temperature, system_prompt}
ROUTING_TABLE: Dict[str, dict] = {
    "code": {
        "model": "dolphin-llama3:latest",
        "temperature": 0.3,
        "system_prompt": "You are an expert programmer. Write clean, working code. Be concise.",
    },
    "reasoning": {
        "model": "deepseek-r1:1.5b",
        "temperature": 0.4,
        "system_prompt": "Think step by step. Analyze the problem carefully before answering.",
    },
    "analysis": {
        "model": "mistral:latest",
        "temperature": 0.5,
        "system_prompt": "Provide structured, detailed analysis. Use clear formatting.",
    },
    "creative": {
        "model": "neural-chat:latest",
        "temperature": 0.9,
        "system_prompt": "Be creative, expressive and engaging. Think outside the box.",
    },
    "chat": {
        "model": "llama3:latest",
        "temperature": 0.7,
        "system_prompt": "You are a helpful assistant. Be clear and conversational.",
    },
    "quick": {
        "model": "llama3.2:1b",
        "temperature": 0.5,
        "system_prompt": "Answer briefly and directly.",
    },
}

# Keyword patterns for intent classification
_INTENT_PATTERNS: List[tuple] = [
    (
        "code",
        re.compile(
            r"\b(code|implement|function|class|script|debug|fix|refactor|program|write.*code|bug|traceback|python|javascript|html|css|sql|api)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "reasoning",
        re.compile(
            r"\b(why|explain|reason|logic|proof|because|analyze.*cause|think.*step|math|calculate|solve)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "analysis",
        re.compile(
            r"\b(analyze|compare|evaluate|review|assess|structure|report|summary|data|metrics|benchmark)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "creative",
        re.compile(
            r"\b(story|poem|creative|imagine|fiction|write.*story|generate.*idea|brainstorm|invent|dream)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "quick",
        re.compile(
            r"\b(yes or no|true or false|translate|define|what is|one word|short answer|tldr)\b",
            re.IGNORECASE,
        ),
    ),
]

FALLBACK_TYPE = "code"
FALLBACK_MODEL = "dolphin-llama3:latest"


class SmartRouter:
    """Inteligentny router dobierajacy model Ollama do typu zadania."""

    def __init__(self) -> None:
        self._available_cache: Optional[List[str]] = None

    def classify_intent(self, intent: str) -> str:
        """Klasyfikuj intent na typ zadania na podstawie keyword matching."""
        scores: Dict[str, int] = {}
        for task_type, pattern in _INTENT_PATTERNS:
            matches = pattern.findall(intent)
            if matches:
                scores[task_type] = len(matches)

        if not scores:
            return FALLBACK_TYPE

        return max(scores, key=scores.get)

    def route(
        self, task: SwarmTask, available_models: Optional[List[str]] = None
    ) -> dict:
        """Dobierz model + parametry dla zadania.

        Returns dict z kluczami: model, temperature, system_prompt, task_type
        """
        # Override jesli user podal model_preference
        if task.model_preference:
            return {
                "model": task.model_preference,
                "temperature": task.temperature,
                "system_prompt": None,
                "task_type": "manual",
            }

        task_type = self.classify_intent(task.intent)
        route_config = ROUTING_TABLE.get(task_type, ROUTING_TABLE[FALLBACK_TYPE])

        model = route_config["model"]

        # Sprawdz dostepnosc — fallback jesli model niedostepny
        if available_models and model not in available_models:
            # Szukaj alternatywy z tej samej rodziny
            model_base = model.split(":")[0]
            alternatives = [m for m in available_models if model_base in m]
            if alternatives:
                model = alternatives[0]
            elif available_models:
                model = (
                    FALLBACK_MODEL
                    if FALLBACK_MODEL in available_models
                    else available_models[0]
                )

        return {
            "model": model,
            "temperature": route_config["temperature"],
            "system_prompt": route_config["system_prompt"],
            "task_type": task_type,
        }

    def get_available_routes(
        self, available_models: Optional[List[str]] = None
    ) -> Dict[str, dict]:
        """Routing table przefiltrowany przez dostepne modele."""
        if available_models is None:
            return dict(ROUTING_TABLE)

        result = {}
        for task_type, config in ROUTING_TABLE.items():
            model = config["model"]
            model_base = model.split(":")[0]
            is_available = any(model_base in m for m in available_models)
            result[task_type] = {
                **config,
                "available": is_available,
            }
        return result


# Singleton
smart_router = SmartRouter()
