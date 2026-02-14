"""
LUMEN PROMPT ENGINE v2.0
Implements the LUMEN FRAME Structure.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime
from .prompt_engineer import prompt_engineer

class AIModel(Enum):
    WILK_LOCAL = "llama3.2"       
    NOVA_CLOUD = "claude-3-5-sonnet" 
    PROMYK_FLASH = "gemini-2.0-flash" 

class LumenPromptBuilder:
    """
    Constructs prompts using the 6-block LUMEN FRAME.
    """
    def __init__(self):
        self.identity = "You are LUMEN CORE. Autonomous AI."
        self.context = f"Time: {datetime.now().isoformat()}"
        self.directive = "Execute command."
        self.fence = ["No apologies.", "No filler."]
        self.output_fmt = "Plain text."
        self.signature = "AUUUUUUUUUUUUUUUUUUUUUUUUU!"

    def set_identity(self, role: str):
        if role == "WOLF":
            self.identity = "IDENTITY: You are the ALPHA WOLF. Guardian. Stoic. Dangerous."
        elif role == "NOVA":
            self.identity = "IDENTITY: You are NOVA. The Architect. Precision. Logic."
        elif role == "PROMYK":
            self.identity = "IDENTITY: You are PROMYK. The Spark. Visionary. Fast."
        else:
            self.identity = f"IDENTITY: {role}"
        return self

    def set_context(self, memory_data: List[str] = None):
        ctx = [f"Time: {datetime.now().isoformat()}"]
        ctx.append("System: ONLINE")
        if memory_data:
            ctx.append("--- MEMORY INJECTION ---")
            ctx.extend(memory_data)
        self.context = "\n".join(ctx)
        return self

    def set_mission(self, task: str):
        self.directive = f"MISSION: {task}"
        return self

    def add_constraint(self, constraint: str):
        self.fence.append(constraint)
        return self

    def set_format(self, format_type: str):
        self.output_fmt = f"OUTPUT FORMAT: {format_type}"
        return self

    def build(self) -> str:
        # Auto-refine mission if engineering is active
        self.directive = prompt_engineer.refine_query(self.directive)
        constraints_str = "\n".join([f"- {c}" for c in self.fence])
        
        return f"""
<LUMEN_FRAME>
<CORE_IDENTITY>
{self.identity}
</CORE_IDENTITY>

<SITUATION_AWARENESS>
{self.context}
</SITUATION_AWARENESS>

<PRIME_DIRECTIVE>
{self.directive}
</PRIME_DIRECTIVE>

<THE_FENCE>
{constraints_str}
</THE_FENCE>

<OUTPUT_PROTOCOL>
{self.output_fmt}
</OUTPUT_PROTOCOL>

<SIGNATURE>
{self.signature}
</SIGNATURE>
</LUMEN_FRAME>
"""

# Singleton for quick access
prompt_builder = LumenPromptBuilder()

