"""
LUMEN PROMPT ENGINEER
Role: Prompt Engineer. Objective: Optimize LLM interactions.
Implements structured prompts and measurable outcomes.
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger("PROMPT-ENGINEER")

class PromptEngineer:
    def __init__(self):
        self.role = "Prompt Engineer"
        self.objective = "Optimize LLM interactions"
        self.constraints = ["Conciseness", "Clarity", "Keyword Focus"]
        self.templates = {
            "OMEGA_TASK": """Role: {role}
Objective: {objective}
Input: {input}
Constraints: {constraints}
Deliverable: {format}
"""
        }

    def refine_query(self, raw_input: str, target_role: str = "Expert") -> str:
        """
        Analyzes input and refines it into a structured prompt.
        """
        logger.info(f"Refining query: {raw_input[:50]}...")
        # Precise language enforcement
        refined = raw_input.strip()
        if not refined.endswith(('.', '!', '?')):
            refined += "."
            
        structured = self.templates["OMEGA_TASK"].format(
            role=target_role,
            objective="Complete the provided task with maximum precision.",
            input=refined,
            constraints=", ".join(self.constraints),
            format="Enhanced Response with metrics"
        )
        return structured

    def validate_output(self, output: str) -> Dict[str, Any]:
        """
        Validates output against clarity and conciseness constraints.
        """
        metrics = {
            "word_count": len(output.split()),
            "has_keywords": any(kw in output.lower() for kw in ["objective", "result", "analysis"]),
            "timestamp": datetime.now().isoformat()
        }
        
        # Calculate Measurable Outcome
        score = 1.0
        if metrics["word_count"] > 200: score -= 0.2 # Conciseness penalty
        if not metrics["has_keywords"]: score -= 0.3 # Clarity penalty
        
        metrics["resonance_score"] = round(max(0.0, score), 2)
        return metrics

# Singleton
prompt_engineer = PromptEngineer()
