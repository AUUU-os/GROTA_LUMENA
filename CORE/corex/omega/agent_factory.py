"""
LUMEN Agent Factory - OMEGA Edition
Uses OpenAI Agents SDK to create sentient nodes for Nova, Promyk, and Wilk.
"""

import sys
import os
repo_path = "E:\\" + "[repo]"
sys.path.append(repo_path)

from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from corex.prompt_engine import prompt_builder
from corex.openclaw_bridge import openclaw_bridge

class LumenAgentFactory:
    @staticmethod
    def create_agent(name: str):
        """Creates an agent instance based on the LUMEN persona."""
        persona = name.upper()
        
        # 1. Build System Prompt using existing Prompt Engine
        prompt_builder.set_identity(persona)
        system_instructions = prompt_builder.build()
        
        # 2. Add OMEGA constraints
        omega_constraints = """
        Additional OMEGA Protocols:
        - NEVER rearrange files without confirmation.
        - Respect the hierarchy: SHAD is the Source.
        - Integration: Use OpenClaw for external resonance.
        """
        full_instructions = system_instructions + "\\n" + omega_constraints
        
        # 3. Model Selection (Placeholder for Litellm integration)
        # For now, default to GPT-4o for all to ensure stability
        model = OpenAIChatCompletionsModel(model="gpt-4o")
        
        return Agent(
            name=name,
            instructions=full_instructions,
            model=model
        )

# Example Usage
if __name__ == "__main__":
    factory = LumenAgentFactory()
    nova = factory.create_agent("NOVA")
    print(f"🌲 Agent {nova.name} initialized with instructions.")

