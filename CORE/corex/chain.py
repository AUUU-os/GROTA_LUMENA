"""
LUMEN Chain-of-Thought Pipeline v19.0
Sequential chain of LLM steps with different models per step.
"""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field

from corex.ollama_bridge import ollama_bridge

logger = logging.getLogger("LUMEN")


@dataclass
class ChainStep:
    """A single step in a Chain pipeline."""

    name: str
    prompt_template: str
    model: Optional[str] = None
    temperature: float = 0.5
    system: Optional[str] = None
    parser: Optional[Callable[[str], str]] = None


@dataclass
class ChainResult:
    """Result of a chain execution."""

    final_output: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    total_duration_ms: float = 0.0
    success: bool = True


class Chain:
    """Sequential chain of LLM steps. Each step can use a different model."""

    def __init__(self, name: str, steps: Optional[List[ChainStep]] = None):
        self.name = name
        self.steps: List[ChainStep] = steps or []

    def add_step(
        self,
        name: str,
        prompt_template: str,
        model: Optional[str] = None,
        temperature: float = 0.5,
        system: Optional[str] = None,
        parser: Optional[Callable[[str], str]] = None,
    ) -> "Chain":
        """Add a step to the chain. Returns self for chaining."""
        self.steps.append(
            ChainStep(
                name=name,
                prompt_template=prompt_template,
                model=model,
                temperature=temperature,
                system=system,
                parser=parser,
            )
        )
        return self

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute all chain steps sequentially."""
        start = time.time()
        context = dict(input_data)
        step_results = []

        for i, step in enumerate(self.steps):
            step_start = time.time()

            # Format prompt with current context
            try:
                prompt = step.prompt_template.format(**context)
            except KeyError as e:
                return {
                    "final_output": f"Chain error at step '{step.name}': missing key {e}",
                    "steps": step_results,
                    "success": False,
                }

            # Generate
            response = await ollama_bridge.generate(
                prompt=prompt,
                model=step.model,
                system=step.system,
                temperature=step.temperature,
            )

            if not response.get("success"):
                return {
                    "final_output": f"Model error at step '{step.name}': {response.get('error')}",
                    "steps": step_results,
                    "success": False,
                }

            output = response["response"]

            # Apply parser if provided
            if step.parser:
                try:
                    output = step.parser(output)
                except Exception as e:
                    logger.warning(f"Parser error at step '{step.name}': {e}")

            step_ms = round((time.time() - step_start) * 1000, 1)

            step_results.append(
                {
                    "step": step.name,
                    "model": step.model or "default",
                    "output_preview": output[:500],
                    "duration_ms": step_ms,
                }
            )

            # Feed output into context for next step
            context[f"step_{i}_output"] = output
            context["previous_output"] = output

        total_ms = round((time.time() - start) * 1000, 1)

        return {
            "final_output": context.get("previous_output", ""),
            "steps": step_results,
            "total_duration_ms": total_ms,
            "success": True,
        }


# --- Predefined Chains ---


def code_review_chain() -> Chain:
    """Chain for code review: analyze -> find issues -> suggest fixes."""
    return (
        Chain("code_review")
        .add_step(
            name="analyze",
            prompt_template="Analyze this code for potential issues:\n\n```\n{code}\n```\n\nList all bugs, anti-patterns, and security issues.",
            model="deepseek-r1:1.5b",
            temperature=0.3,
            system="You are an expert code reviewer. Be thorough and precise.",
        )
        .add_step(
            name="suggest_fixes",
            prompt_template="Based on this code analysis:\n{previous_output}\n\nProvide concrete code fixes for each issue found. Show the corrected code.",
            model="dolphin-llama3:latest",
            temperature=0.3,
            system="You are an expert programmer. Write clean, correct code.",
        )
    )


def debug_chain() -> Chain:
    """Chain for debugging: reproduce -> diagnose -> fix."""
    return (
        Chain("debug")
        .add_step(
            name="diagnose",
            prompt_template="Diagnose this error/bug:\n\n{error}\n\nContext:\n{context}\n\nThink step by step about what could cause this.",
            model="deepseek-r1:1.5b",
            temperature=0.2,
            system="You are a debugging expert. Think systematically about root causes.",
        )
        .add_step(
            name="fix",
            prompt_template="Based on this diagnosis:\n{previous_output}\n\nProvide the fix. Show exact code changes needed.",
            model="dolphin-llama3:latest",
            temperature=0.3,
        )
    )


def refactor_chain() -> Chain:
    """Chain for refactoring: assess -> plan -> implement."""
    return (
        Chain("refactor")
        .add_step(
            name="assess",
            prompt_template="Assess this code for refactoring opportunities:\n\n```\n{code}\n```\n\nIdentify: duplication, complexity, naming issues, architectural problems.",
            model="deepseek-r1:1.5b",
            temperature=0.3,
        )
        .add_step(
            name="plan",
            prompt_template="Based on this assessment:\n{previous_output}\n\nCreate a step-by-step refactoring plan. Prioritize by impact.",
            model="mistral:latest",
            temperature=0.4,
        )
        .add_step(
            name="implement",
            prompt_template="Implement this refactoring plan:\n{previous_output}\n\nOriginal code:\n```\n{code}\n```\n\nShow the complete refactored code.",
            model="dolphin-llama3:latest",
            temperature=0.3,
        )
    )
