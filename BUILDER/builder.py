"""
Builder — Central Orchestrator for GROTA LUMENA.

Entry point: starts the FastAPI daemon on port 8800.
Usage: python -m BUILDER.builder
"""

import sys
import logging
from pathlib import Path

# Ensure GROTA_LUMENA root is on path
grota_root = Path(__file__).resolve().parent.parent
if str(grota_root) not in sys.path:
    sys.path.insert(0, str(grota_root))

from BUILDER.config import HOST, PORT, VERSION

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("builder")


def main():
    import uvicorn
    from BUILDER.api.app import create_app

    app = create_app()

    banner = (
        f"\n"
        f"    ================================================\n"
        f"      BUILDER v{VERSION} -- GROTA LUMENA\n"
        f"      Centralny Orkiestrator Watahy\n"
        f"      http://{HOST}:{PORT}\n"
        f"      AUUUUUUUUUUUUUUUUUUU!\n"
        f"    ================================================\n"
    )
    print(banner)

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
