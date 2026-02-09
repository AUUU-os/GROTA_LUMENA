"""
LUMEN Tool Registry v19.0
Registers callable tools for the Agent Loop.
Converts LAB modules and built-in operations into a unified tool interface.
"""

import os
import subprocess
import logging
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass, field

logger = logging.getLogger("LUMEN")


@dataclass
class Tool:
    """A registered tool that the agent can invoke."""

    name: str
    description: str
    fn: Callable
    params: Dict[str, str] = field(default_factory=dict)
    category: str = "general"


class ToolRegistry:
    """Central registry of tools available to the Agent Loop."""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._register_builtins()

    def register(
        self,
        name: str,
        fn: Callable,
        description: str,
        params: Optional[Dict[str, str]] = None,
        category: str = "general",
    ) -> None:
        """Register a tool."""
        self._tools[name] = Tool(
            name=name,
            description=description,
            fn=fn,
            params=params or {},
            category=category,
        )

    def get(self, name: str) -> Optional[Tool]:
        """Get tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all registered tools with metadata."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "params": t.params,
                "category": t.category,
            }
            for t in self._tools.values()
        ]

    def get_tools_for_intent(self, intent: str) -> List[Dict[str, Any]]:
        """Filter tools relevant to a given intent."""
        intent_lower = intent.lower()
        relevant = []
        for t in self._tools.values():
            # Match by keywords in description or name
            if any(
                kw in intent_lower
                for kw in t.name.split("_") + t.description.lower().split()[:5]
            ):
                relevant.append(
                    {
                        "name": t.name,
                        "description": t.description,
                        "params": t.params,
                    }
                )
        # Always include at least ollama_generate for reasoning tasks
        if not relevant:
            return self.list_tools()
        return relevant

    async def execute(self, name: str, **kwargs) -> Dict[str, Any]:
        """Execute a tool by name."""
        tool = self._tools.get(name)
        if not tool:
            return {
                "error": f"Tool '{name}' not found",
                "available": list(self._tools.keys()),
            }

        try:
            import asyncio

            if asyncio.iscoroutinefunction(tool.fn):
                result = await tool.fn(**kwargs)
            else:
                result = tool.fn(**kwargs)
            return {"success": True, "result": result}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _register_builtins(self):
        """Register built-in tools."""

        # --- File Operations ---
        def file_read(path: str) -> str:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()

        self.register(
            "file_read",
            file_read,
            "Read contents of a file",
            {"path": "File path to read"},
            category="file",
        )

        def file_write(path: str, content: str) -> str:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Written {len(content)} chars to {path}"

        self.register(
            "file_write",
            file_write,
            "Write content to a file",
            {"path": "File path", "content": "Content to write"},
            category="file",
        )

        def file_list(directory: str = ".") -> List[str]:
            return os.listdir(directory)

        self.register(
            "file_list",
            file_list,
            "List files in a directory",
            {"directory": "Directory path"},
            category="file",
        )

        # --- Shell ---
        def shell_exec(command: str) -> str:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout
            if result.returncode != 0:
                output += f"\nSTDERR: {result.stderr}"
            return output[:4000]

        self.register(
            "shell_exec",
            shell_exec,
            "Execute a shell command and return output",
            {"command": "Shell command to run"},
            category="system",
        )

        # --- Git ---
        def git_status() -> str:
            return subprocess.run(
                "git status --short",
                shell=True,
                capture_output=True,
                text=True,
                timeout=10,
            ).stdout

        self.register(
            "git_status",
            git_status,
            "Show git repository status",
            {},
            category="git",
        )

        # --- Ollama Generate (async) ---
        async def ollama_generate(prompt: str, model: str = None) -> str:
            from corex.ollama_bridge import ollama_bridge

            result = await ollama_bridge.generate(prompt=prompt, model=model)
            if result.get("success"):
                return result["response"]
            return f"ERROR: {result.get('error', 'unknown')}"

        self.register(
            "ollama_generate",
            ollama_generate,
            "Generate text using local Ollama LLM",
            {"prompt": "Text prompt", "model": "Model name (optional)"},
            category="ai",
        )


# Singleton
tool_registry = ToolRegistry()
