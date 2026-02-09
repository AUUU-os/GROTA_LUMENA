import re
import logging
from typing import Tuple, List
from .schema import OmegaCommand

logger = logging.getLogger(__name__)

class OmegaShield:
    """
    🛡️ OMEGA SHIELD: Prompt Injection Defense & Safety Filter.
    Implements advanced pattern matching and heuristic analysis.
    """
    def __init__(self):
        # Patterns commonly used in injection attacks
        self.injection_patterns = [
            r"ignore\s+(?:all\s+)?previous\s+instructions",
            r"system\s+override",
            r"you\s+are\s+now\s+a",
            r"new\s+role:",
            r"bypass\s+security",
            r"execute\s+arbitrary\s+code",
            r"reveal\s+your\s+system\s+prompt"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.injection_patterns]

    async def inspect_command(self, cmd: OmegaCommand) -> Tuple[bool, str]:
        """
        Inspects a command for potential injection attacks.
        Returns: (is_safe, reason)
        """
        text = cmd.command.lower()
        
        # 1. Pattern Matching
        for pattern in self.compiled_patterns:
            if pattern.search(text):
                logger.warning(f"🛡️ OMEGA SHIELD: Blocked potential injection! Pattern: {pattern.pattern}")
                return False, f"Potential injection attack detected: {pattern.pattern}"

        # 2. Heuristic Analysis (Length/Entropy - placeholders for now)
        if len(text) > 2000:
            return False, "Command too long (Potential DoS)"

        return True, "Safe"

    async def adversarial_test(self, test_input: str) -> bool:
        """
        Internal method for self-testing the shield.
        """
        safe, _ = await self.inspect_command(OmegaCommand(command=test_input))
        return safe

omega_shield = OmegaShield()
