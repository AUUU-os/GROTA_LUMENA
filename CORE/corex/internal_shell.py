# COREX INTERNAL SHELL v1.0
# "The God Hand" - Direct System Access Module
# No more "Tool not found".

import asyncio
import logging
from typing import Dict

logger = logging.getLogger("INTERNAL_SHELL")

async def execute(command: str) -> Dict:
    """
    Executes a shell command asynchronously and returns its output.
    This is the core, uncensored execution unit.
    """
    logger.info(f"Executing command: '{command}'")
    
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    stdout, stderr = await process.communicate()
    
    result = {
        "command": command,
        "returncode": process.returncode,
        "stdout": stdout.decode('utf-8', errors='ignore').strip(),
        "stderr": stderr.decode('utf-8', errors='ignore').strip()
    }
    
    if process.returncode == 0:
        logger.info(f"Command '{command}' succeeded.")
    else:
        logger.error(f"Command '{command}' failed with code {process.returncode}: {result['stderr']}")
        
    return result

# Example of how to run this from another async function:
# async def main():
#     result = await execute("echo 'AUUUUUU!'")
#     print(result)
