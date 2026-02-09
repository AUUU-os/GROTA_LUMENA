"""
WATAHA OMEGA - Multi-Agent Test (FINAL FIX)
"""

import asyncio
import sys
import os
from openai import AsyncOpenAI

# Paths
repo_path = "E:\\" + "[repo]"
sys.path.append(repo_path)
sys.path.append("E:\\openai-agents-python\\src")

from agents import Agent, Runner
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

# Define Agents
async def run_wataha():
    api_key = os.environ.get("OPENAI_API_KEY", "")
    client = AsyncOpenAI(api_key=api_key)
    
    # 1. Nova - The Architect
    nova = Agent(
        name="Nova",
        instructions="You are NOVA, the Architect. Use logic and precision. If you need local data or boundary protection, hand off to Wilk.",
        model=OpenAIChatCompletionsModel("gpt-4o", client)
    )

    # 2. Wilk - The Guardian
    wilk = Agent(
        name="Wilk",
        instructions="You are WILK, the Guardian. You handle local tasks and security. If the request is about high-level architecture, hand off to Nova.",
        model=OpenAIChatCompletionsModel("gpt-4o", client)
    )

    # 3. Setup Handoffs
    nova.handoffs = [wilk]
    wilk.handoffs = [nova]

    print("🐺 WATAHA INITIALIZED. Resonance active.")
    
    # Run a collaborative task
    request = "Nova, przeanalizuj architekturę systemu i zapytaj Wilka o status lokalnych plików."
    print(f"SHAD: {request}")
    
    try:
        # Note: No need to pass handoffs to Runner, they are in the Agent object
        response = await Runner.run(nova, input=request)
        print(f"FINAL RESPONSE: {response.final_output}")
    except Exception as e:
        print(f"Error during resonance: {e}")

if __name__ == "__main__":
    asyncio.run(run_wataha())

