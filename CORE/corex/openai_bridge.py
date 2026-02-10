"""
LUMEN OpenAI Bridge
Connects the system to OpenAI's GPT models with tool-calling capabilities.
Bypasses the need for CustomGPT by acting as a standalone 'LUMEN GPT' app.
"""

import os
import json
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI
from corex.config import settings
from corex.memory_engine import memory_engine

logger = logging.getLogger(__name__)

class OpenAIBridge:
    def __init__(self, daemon=None):
        self.daemon = daemon
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None
        self.model = "gpt-4o" # Default high-power model

    def is_active(self) -> bool:
        return self.client is not None

    async def chat(self, message: str, history: List[Dict[str, str]] = None) -> str:
        """
        Send a message to GPT-4o with LUMEN tools enabled.
        """
        if not self.client:
            return "OpenAI API Key not configured. Please check your .env file."

        messages = history or []
        # Inject memory context (RAG)
        try:
            mem = await memory_engine.retrieve_memories(
                query=message, limit=5, strategy="hybrid"
            )
            mem_lines = [m.get("content", "") for m in mem if m.get("content")]
            if mem_lines:
                # Hard limit to prevent prompt bloat
                joined = "\n- ".join(mem_lines)
                if len(joined) > 1500:
                    joined = joined[:1500] + "..."
                messages.insert(
                    0,
                    {
                        "role": "system",
                        "content": "Memory context:\n- " + joined,
                    },
                )
        except Exception:
            pass
        messages.append({"role": "user", "content": message})

        # Define tools (Function Calling)
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "generate_wolf_script",
                    "description": "Generates a high-vibration Wolf video script with a specific number of scenes.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "num_scenes": {"type": "integer", "description": "Number of scenes to generate"}
                        },
                        "required": ["num_scenes"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_chronicle",
                    "description": "Searches the system memory (Chronicle) for historical events or information.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search term or question about system history"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools,
                tool_choice="auto"
            )

            response_message = response.choices[0].message
            tool_calls = response_message.tool_calls

            if tool_calls:
                # Handle tool calls
                messages.append(response_message)
                for tool_call in tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)
                    
                    logger.info(f"GPT calling tool: {function_name}({function_args})")
                    
                    # Execute tool via Daemon
                    tool_result = await self._execute_tool(function_name, function_args)
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(tool_result)
                    })

                # Get final response from GPT after tool execution
                second_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
                return second_response.choices[0].message.content

            return response_message.content

        except Exception as e:
            logger.error(f"OpenAI Bridge Error: {e}")
            return f"Error communicating with OpenAI: {str(e)}"

    async def _execute_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Maps GPT tool calls to internal LUMEN operations."""
        if not self.daemon:
            return {"success": False, "error": "Daemon not connected to bridge."}

        if name == "generate_wolf_script":
            return await self.daemon.execute_command(f"generate wolf script with {args.get('num_scenes', 3)} scenes")
        
        if name == "query_chronicle":
            # Direct query to audit logger
            history = self.daemon.audit.query(limit=10)
            return {"success": True, "data": history}

        return {"success": False, "error": f"Tool {name} not implemented."}

# Singleton
openai_bridge = OpenAIBridge()
