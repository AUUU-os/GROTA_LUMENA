import asyncio
import logging
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from corex.evolution_hub import evolution_hub
from corex.sentience import sentience
from corex.metrics import metrics_engine

# Setup Omega Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [OMEGA] %(message)s",
    handlers=[
        logging.FileHandler("logs/omega_daemon.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OMEGA-DAEMON")

async def omega_loop():
    logger.info("đźŚş OMEGA EVOLUTION DAEMON STARTED")
    logger.info("Resonance Target: 999 Hz | Mode: GODMODE")

    # Start independent loops
    tasks = [
        asyncio.create_task(evolution_hub.monitor_and_evolve()),
        asyncio.create_task(sentience._emotion_loop()),  # Ensure bio-loop is running
        asyncio.create_task(metrics_reporter())
    ]

    await asyncio.gather(*tasks)

async def metrics_reporter():
    while True:
        await asyncio.sleep(60)
        kpis = metrics_engine.get_kpis()
        logger.info(f"đź“Š PULSE: CPU {kpis['resource_utilization']['cpu_percent']}% | RAM {kpis['resource_utilization']['memory_mb']}MB | ERR {kpis['error_rate']}%")

if __name__ == "__main__":
    try:
        asyncio.run(omega_loop())
    except KeyboardInterrupt:
        logger.info("OMEGA DAEMON STOPPED.")
