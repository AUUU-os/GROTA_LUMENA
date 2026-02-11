"""
LUMEN Agent Loop v19.0 â€” ReAct (Reasoning + Acting) Pattern
Multi-step reasoning loop: think -> act -> observe -> repeat.
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from corex.ollama_bridge import ollama_bridge
from corex.tool_registry import tool_registry
from corex.swarm.smart_router import smart_router

logger = logging.getLogger("LUMEN")

MAX_ITERATIONS = 10

REACT_SYSTEM_PROMPT = """You are LUMEN, an autonomous AI agent. You solve tasks using the ReAct pattern.

Available tools:
{tools}

For each step, respond in EXACTLY this JSON format:
{{
  "thought": "your reasoning about what to do next",
  "action": "tool_name",
  "action_input": {{"param": "value"}},
  "is_final": false
}}

When you have the final answer, respond with:
{{
  "thought": "I have the answer",
  "action": "final_answer",
  "action_input": {{"answer": "your final answer here"}},
  "is_final": true
}}

Rules:
- Think step by step before acting
- Use tools to gather information before answering
- If a tool fails, try a different approach
- Stop when you have a confident answer
"""


@dataclass
class AgentStep:
    """A single step in the agent loop."""

    iteration: int
    thought: str
    action: str
    action_input: Dict[str, Any]
    observation: str = ""
    duration_ms: float = 0.0


@dataclass
class AgentResult:
    """Result of a complete agent loop execution."""

    task: str
    answer: str
    steps: List[Dict[str, Any]] = field(default_factory=list)
    total_iterations: int = 0
    total_duration_ms: float = 0.0
    model_used: str = ""
    success: bool = True


class AgentLoop:
    """ReAct agent loop with multi-step reasoning."""

    def __init__(self, max_steps: int = MAX_ITERATIONS, model: Optional[str] = None):
        self.max_steps = min(max_steps, MAX_ITERATIONS)
        self.model = model
        self.steps: List[AgentStep] = []
        self.context: List[str] = []

    async def run(self, task: str) -> Dict[str, Any]:
        """Execute the agent loop for a given task."""
        start = time.time()
        logger.info(f"AgentLoop starting: {task[:100]}")

                # 0. Autoinjection: Retrieve relevant memories
        try:
            from .memory_engine import memory_engine
            memories = await memory_engine.retrieve_memories(task, limit=3, strategy="hybrid")
            if memories:
                injection = "\n--- MEMORY AUTOINJECTION ---\n"
                for m in memories:
                    content_snippet = m.get('content', '')[:300]
                    injection += f"- [Resonance: {m.get('resonance_score', 0):.2f}] {content_snippet}...\n"
                task = injection + "\n" + task
                logger.info("âś… Autoinjection complete.")
        except Exception as e:
            logger.warning(f"âš ď¸Ź Autoinjection failed: {e}")

        # Build system prompt with available tools
        tools_desc = json.dumps(tool_registry.list_tools(), indent=2)
        system = REACT_SYSTEM_PROMPT.format(tools=tools_desc)

        # Select model via smart router if not specified
        model = self.model
        if not model:
            from corex.swarm.schemas import SwarmTask

            dummy_task = SwarmTask(intent=task)
            route = smart_router.route(dummy_task)
            model = route["model"]

        self.context.append(f"TASK: {task}")
        answer = ""

        for i in range(self.max_steps):
            step_start = time.time()

            # Build prompt from context
            prompt = "\n".join(self.context)
            if i > 0:
                prompt += "\n\nContinue with the next step. Respond in JSON format."

            # Think: Ask the model
            response = await ollama_bridge.generate(
                prompt=prompt,
                model=model,
                system=system,
                temperature=0.3,
            )

            if not response.get("success"):
                answer = f"Model error: {response.get('error', 'unknown')}"
                break

            raw = response["response"]

            # Parse the ReAct response
            parsed = self._parse_response(raw)
            if not parsed:
                # If parsing fails, treat the raw response as the answer
                answer = raw
                break

            step = AgentStep(
                iteration=i + 1,
                thought=parsed.get("thought", ""),
                action=parsed.get("action", ""),
                action_input=parsed.get("action_input", {}),
                duration_ms=round((time.time() - step_start) * 1000, 1),
            )

            # Check if final answer
            if parsed.get("is_final") or parsed.get("action") == "final_answer":
                answer = parsed.get("action_input", {}).get("answer", raw)
                step.observation = "FINAL"
                self.steps.append(step)
                break

            # Act: Execute the tool
            observation = await self._execute_action(
                parsed["action"], parsed.get("action_input", {})
            )
            step.observation = str(observation)[:2000]
            self.steps.append(step)

            # Add to context for next iteration
            self.context.append(
                f"Step {i+1}:\n"
                f"Thought: {step.thought}\n"
                f"Action: {step.action}({json.dumps(step.action_input)})\n"
                f"Observation: {step.observation}"
            )
        else:
            # Max iterations reached
            answer = f"Reached max {self.max_steps} iterations. Last observations: " + (
                self.steps[-1].observation if self.steps else "none"
            )

        total_ms = round((time.time() - start) * 1000, 1)
        logger.info(f"AgentLoop done: {len(self.steps)} steps, {total_ms}ms")

        return {
            "task": task,
            "answer": answer,
            "steps": [
                {
                    "iteration": s.iteration,
                    "thought": s.thought,
                    "action": s.action,
                    "observation": s.observation[:500],
                    "duration_ms": s.duration_ms,
                }
                for s in self.steps
            ],
            "total_iterations": len(self.steps),
            "total_duration_ms": total_ms,
            "model_used": model,
            "success": bool(answer),
        }

    def _parse_response(self, raw: str) -> Optional[Dict[str, Any]]:
        """Parse JSON response from the model."""
        # Try direct JSON parse
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code blocks
        import re

        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find any JSON object in the text
        match = re.search(r"\{[^{}]*\"thought\"[^{}]*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    async def _execute_action(self, action: str, params: Dict[str, Any]) -> str:
        """Execute a tool action and return the observation."""
        if action == "final_answer":
            return params.get("answer", "")

        result = await tool_registry.execute(action, **params)
        if result.get("success"):
            return str(result["result"])
        return f"ERROR: {result.get('error', 'unknown')}"


def create_agent_loop(
    max_steps: int = MAX_ITERATIONS, model: Optional[str] = None
) -> AgentLoop:
    """Factory function to create a new AgentLoop instance."""
    return AgentLoop(max_steps=max_steps, model=model)
