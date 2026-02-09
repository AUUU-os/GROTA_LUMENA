"""
Ollama Bridge — async integration with local Ollama (localhost:11434).
Reuses patterns from CORE/corex/ollama_bridge.py.
"""
from __future__ import annotations

import logging
import aiohttp

from BUILDER.config import OLLAMA_URL, OLLAMA_TIMEOUT, OLLAMA_DEFAULT_MODEL
from BUILDER.core.task_manager import Task

logger = logging.getLogger("builder.bridge.ollama")


class OllamaBridge:
    def __init__(self, base_url: str | None = None):
        self.base_url = base_url or OLLAMA_URL
        self.timeout = aiohttp.ClientTimeout(total=OLLAMA_TIMEOUT)

    async def health(self) -> bool:
        """Check if Ollama is responding."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def list_models(self) -> list[str]:
        """Get available local models."""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    async def execute(
        self,
        task: Task,
        model: str | None = None,
        temperature: float = 0.7,
        system_prompt: str | None = None,
    ) -> dict:
        """Execute a task via Ollama generate API."""
        target_model = model or OLLAMA_DEFAULT_MODEL
        prompt = f"# Task: {task.title}\n\n{task.description}"

        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_ctx": 8192,
                "temperature": temperature,
                "top_k": 40,
                "top_p": 0.9,
                "num_predict": 2048,
            },
        }

        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "success": True,
                            "model": target_model,
                            "response": data.get("response", ""),
                            "metrics": {
                                "eval_count": data.get("eval_count"),
                                "eval_duration": data.get("eval_duration"),
                            },
                        }
                    return {"success": False, "error": f"Ollama HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Ollama execution failed: {e}")
            return {"success": False, "error": str(e)}
