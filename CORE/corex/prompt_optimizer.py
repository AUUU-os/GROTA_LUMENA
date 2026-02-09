"""
LUMEN PROMPT OPTIMIZER
Measures adherence to constraints and response quality.
"""

import re
import json
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class PromptOptimizer:
    def __init__(self):
        # Negative constraints to check (Things models should NEVER say)
        self.forbidden_patterns = [
            r"as an ai language model",
            r"i apologize",
            r"i'm sorry",
            r"sorry for the confusion",
            r"i am just a computer program"
        ]

    def validate_response(self, prompt_name: str, response_text: str, expected_format: str = "text") -> Dict[str, Any]:
        """
        Validates if the response meets LUMEN standards.
        """
        text_lower = response_text.lower()
        violations = []

        # 1. Check Negative Constraints
        for pattern in self.forbidden_patterns:
            if re.search(pattern, text_lower):
                violations.append(f"Forbidden phrase detected: {pattern}")

        # 2. Format Validation
        format_passed = True
        if expected_format == "json":
            try:
                json.loads(response_text)
            except:
                format_passed = False
                violations.append("Failed JSON format validation")
        elif expected_format == "xml":
            if not (response_text.startswith("<") and response_text.endswith(">")):
                format_passed = False
                violations.append("Failed XML-like structure validation")

        # 3. Vibe Check (Wolf specific)
        vibe_score = 1.0
        if "wolf" in prompt_name:
            if "auuuuu" not in text_lower:
                vibe_score -= 0.3
                violations.append("Missing resonance signal (AUUUUU)")
            if len(response_text.split()) > 50: # Wolf should be concise
                vibe_score -= 0.2
                violations.append("Response too verbose for Wolf archetype")

        score = max(0.0, 1.0 - (len(violations) * 0.2))
        
        return {
            "prompt_name": prompt_name,
            "pass": len(violations) == 0,
            "score": round(score, 2),
            "vibe_score": round(vibe_score, 2),
            "violations": violations,
            "latency_ms": 0 # Placeholder for benchmark
        }

# Singleton
prompt_optimizer = PromptOptimizer()
