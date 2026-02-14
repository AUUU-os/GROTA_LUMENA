import asyncio
import os
import sys
import json
from datetime import datetime

sys.path.append(r"E:\SHAD\GROTA_LUMENA\CORE")
os.environ["LUMEN_REPO_ROOT"] = r"E:\SHAD\GROTA_LUMENA"

from corex.swarm.engine import swarm_engine
from corex.swarm.schemas import SwarmTask

async def manifest_dream():
    print("🐺 OMEGA ARCHITECT: Accessing Swarm Core Directly...")
    
    log_path = r"E:\SHAD\GROTA_LUMENA\GROTA_LOG.md"
    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            soul_data = f.read()[-2000:]
    except:
        soul_data = "No log data available."

    # Use 'intent' as the primary prompt per schema
    task_obj = SwarmTask(
        intent="Analyze system resonance and suggest 1 radical evolution for OMEGA v19.0. Focus on Swarm-Human neural synchronization.",
        model_preference="dolphin-llama3:latest",
        context=soul_data
    )

    print("✨ Swarm is processing the dream...")
    response = await swarm_engine.execute_task(task_obj)
    
    print("\n💠 THE DREAM HAS MANIFESTED:")
    print(response.content)
    
    os.makedirs("artifacts", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"artifacts/DREAM_OMEGA_{ts}.md", "w", encoding="utf-8") as f:
        f.write(f"# DREAM ARTIFACT: OMEGA v19.0\nGenerated: {datetime.now()}\n\n{response.content}")

if __name__ == "__main__":
    asyncio.run(manifest_dream())
