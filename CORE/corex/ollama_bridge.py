"""
LUMEN OLLAMA BRIDGE (GPU EDITION v2)
Optimized for RTX 2070 Super. 
Supports: Dolphin (Uncensored), DeepSeek (Reasoning).
Features: Caching, JSON Mode, Dynamic Model Selection.
"""

import aiohttp
import logging
import json
import time
from typing import Dict, Any, Optional, List

logger = logging.getLogger("LUMEN-OLLAMA")

class OllamaBridge:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.default_model = "dolphin-llama3:latest"
        self.reasoning_model = "deepseek-coder:6.7b" # Or equivalent local model
        self.gpu_layers = 35 
        self.context_window = 8192
        self._cache = {}
        self._cache_ttl = 300 # 5 minutes

    async def get_models(self) -> List[str]:
        """Fetch available local models."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/tags") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return [m['name'] for m in data.get('models', [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    async def generate(self, 
                       prompt: str, 
                       model: Optional[str] = None, 
                       system: Optional[str] = None,
                       format: str = None, # 'json' or None
                       temperature: float = 0.7) -> Dict[str, Any]:
        
        # 1. Check Cache (Memoization)
        cache_key = f"{model}:{prompt}:{format}"
        if cache_key in self._cache:
            entry = self._cache[cache_key]
            if time.time() - entry['ts'] < self._cache_ttl:
                logger.debug("⚡ Cache Hit for Ollama request")
                return entry['data']

        # 2. Select Model
        target_model = model or self.default_model
        
        payload = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "format": format,
            "options": {
                "num_ctx": self.context_window,
                "num_gpu": self.gpu_layers,
                "temperature": temperature,
                "top_k": 40,
                "top_p": 0.9,
                "num_predict": 1024 # Limit output tokens
            }
        }
        
        if system:
            payload["system"] = system

        # 3. Request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.base_url}/api/generate", json=payload) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        result = {
                            "success": True, 
                            "model": target_model,
                            "response": data.get("response", ""),
                            "metrics": {
                                "eval_count": data.get("eval_count"),
                                "eval_duration": data.get("eval_duration")
                            }
                        }
                        
                        # Cache Result
                        self._cache[cache_key] = {"ts": time.time(), "data": result}
                        return result
                    
                    return {"success": False, "error": f"Ollama Error: {resp.status}"}
        except Exception as e:
            logger.error(f"Ollama Connection Failed: {e}")
            return {"success": False, "error": str(e)}

ollama_bridge = OllamaBridge()
