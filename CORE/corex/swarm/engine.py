from langsmith import traceable
import asyncio
import json
import time
import aiohttp
from collections import deque
from typing import List, Optional
from datetime import datetime
from .schemas import SwarmTask, AgentResponse, TaskResult
from .smart_router import smart_router

# Local config
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
DEFAULT_MODEL = "dolphin-llama3:latest"

LIVE_BRIDGE_MESSAGES = "E:/[runtime]core-x-agent/LIVE_BRIDGE/MESSAGES.jsonl"

# Retry backoff: attempt 0 = 0s, attempt 1 = 1s, attempt 2 = 3s
RETRY_BACKOFF = [0, 1, 3]

MAX_HISTORY = 200


class SwarmEngine:
    def __init__(self) -> None:
        self._task_history: deque[TaskResult] = deque(maxlen=MAX_HISTORY)
        self._queue_size: int = 0

    async def list_agents(self) -> List[str]:
        """Fetch available models from Ollama."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    OLLAMA_TAGS_URL, timeout=aiohttp.ClientTimeout(total=5)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m["name"] for m in data.get("models", [])]
        except Exception:
            return ["offline"]
        return []

    async def ping_ollama(self) -> bool:
        """Quick Ollama availability check."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    OLLAMA_TAGS_URL, timeout=aiohttp.ClientTimeout(total=3)
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def check_model_health(self, model: str) -> Optional[float]:
        """Ping a model with trivial prompt, return response time in ms or None."""
        payload = {
            "model": model,
            "prompt": "Hi",
            "stream": False,
            "options": {"num_predict": 1},
        }
        try:
            start = time.time()
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OLLAMA_URL, json=payload, timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        return round((time.time() - start) * 1000, 1)
        except Exception:
            pass
        return None

    @traceable(name="Swarm Task Execution", project_name="LUMENA_OMEGA_v19")
    async def execute_task(self, task: SwarmTask) -> AgentResponse:
        """Dispatch task with smart routing and retry logic."""
        self._queue_size += 1
        start_time = time.time()
        retries_used = 0

        # Smart routing
        available_models = await self.list_agents()
        is_online = available_models != ["offline"]
        route_info = smart_router.route(task, available_models if is_online else None)

        target_model = route_info["model"]
        system_prompt = route_info.get("system_prompt")
        task_type = route_info.get("task_type", "unknown")
        agent_role = route_info.get("agent_role", "codex")

        # Build prompt
        prompt_parts = []
        if system_prompt:
            prompt_parts.append(f"SYSTEM: {system_prompt}")
        prompt_parts.append(f"TASK: {task.intent}")
        if task.context:
            prompt_parts.append(f"CONTEXT: {task.context}")

        full_prompt = "\n".join(prompt_parts)

        payload = {
            "model": target_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {"temperature": route_info.get("temperature", task.temperature)},
        }

        content = ""
        duration = 0.0
        success = False

        # Execute with retry
        max_attempts = 1 + task.max_retries
        for attempt in range(max_attempts):
            if attempt > 0:
                backoff = RETRY_BACKOFF[min(attempt, len(RETRY_BACKOFF) - 1)]
                await asyncio.sleep(backoff)
                retries_used = attempt

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        OLLAMA_URL,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=120),
                    ) as resp:
                        if resp.status == 200:
                            result = await resp.json()
                            content = result.get("response", "")
                            duration = result.get("total_duration", 0) / 1e9
                            success = True
                            break
                        else:
                            content = f"ERROR: Ollama returned {resp.status}"
            except Exception as e:
                content = f"CRITICAL ERROR: {str(e)}"

        exec_time = time.time() - start_time
        self._queue_size = max(0, self._queue_size - 1)

        response = AgentResponse(
            agent_name=agent_role,
            model_used=target_model,
            content=content,
            execution_time=round(exec_time, 3),
            metadata={
                "raw_duration": duration,
                "task_type": task_type,
                "routed_by": "smart_router" if not task.model_preference else "manual",
                "agent_role": agent_role,
                "priority": task.priority.name,
                "retries_used": retries_used,
                "success": success,
            },
        )

        # Track history
        self._task_history.append(
            TaskResult(
                task_intent=task.intent[:120],
                task_type=task_type,
                model_used=target_model,
                priority=task.priority,
                success=success,
                retries_used=retries_used,
                execution_time=round(exec_time, 3),
            )
        )

        # Log to LIVE_BRIDGE
        self._log_to_bridge(task, response, task_type)

        return response

    def get_task_history(self, limit: int = 20) -> List[TaskResult]:
        """Return recent task history."""
        items = list(self._task_history)
        return items[-limit:]

    @property
    def queue_size(self) -> int:
        return self._queue_size

    def _log_to_bridge(
        self, task: SwarmTask, response: AgentResponse, task_type: str
    ) -> None:
        """Append routing log to LIVE_BRIDGE/MESSAGES.jsonl."""
        msg = {
            "from": "swarm_router",
            "to": "all",
            "message": f"[ROUTED] {task_type} -> {response.model_used} | P:{task.priority.name} | {task.intent[:80]}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "metadata": {
                "task_type": task_type,
                "model": response.model_used,
                "exec_time": response.execution_time,
                "priority": task.priority.name,
                "retries": response.metadata.get("retries_used", 0),
            },
        }
        try:
            with open(LIVE_BRIDGE_MESSAGES, "a", encoding="utf-8") as f:
                f.write(json.dumps(msg) + "\n")
        except Exception:
            pass

    async def execute_with_tools(self, task: SwarmTask) -> AgentResponse:
        """Execute a task using ToolRegistry for tool-augmented generation.

        Combines SwarmEngine's Ollama execution with ToolRegistry,
        allowing the agent loop to use registered tools during task execution.
        """
        from corex.tool_registry import tool_registry

        # Get relevant tools for the task
        relevant_tools = tool_registry.get_tools_for_intent(task.intent)
        tool_descriptions = "\n".join(
            f"- {t['name']}: {t['description']}" for t in relevant_tools
        )

        # Augment task with tool context
        augmented_task = SwarmTask(
            intent=task.intent,
            context=f"{task.context or ''}\n\nAvailable tools:\n{tool_descriptions}".strip(),
            model_preference=task.model_preference,
            temperature=task.temperature,
            priority=task.priority,
            max_retries=task.max_retries,
        )

        return await self.execute_task(augmented_task)


swarm_engine = SwarmEngine()
