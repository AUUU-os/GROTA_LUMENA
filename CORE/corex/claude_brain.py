"""
Claude Brain Module
Intelligent command understanding and response generation using Claude API
"""

import sys
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# Try to import Anthropic SDK
try:
    from anthropic import Anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  Anthropic SDK not installed. Install with: pip install anthropic")


@dataclass
class ClaudeIntent:
    """
    Intent extracted by Claude Brain
    """
    understood: bool  # Did Claude understand the request?
    commands: List[str]  # Commands to execute (e.g., ["show git status", "show git diff"])
    reasoning: str  # Claude's reasoning about what user wants
    confidence: float  # Confidence in understanding (0.0-1.0)
    natural_request: str  # Original natural language request


class ClaudeBrain:
    """
    Claude Brain - Intelligent command understanding with Claude API

    Replaces simple pattern matching with actual AI understanding.

    Example:
        brain = ClaudeBrain()
        intent = await brain.understand("what changed in my code today?")
        # Returns: ClaudeIntent with commands=["show git status", "show git diff"]
    """

    def __init__(self, model: str = "claude-sonnet-4-5-20250929"):
        """
        Initialize Claude Brain

        Args:
            model: Claude model to use
        """
        self.model = model

        # Load API key
        self._load_api_key()

        # Check availability
        self.enabled = ANTHROPIC_AVAILABLE and self.api_key is not None

        if not self.enabled:
            if not ANTHROPIC_AVAILABLE:
                print("⚠️  Claude Brain disabled: anthropic package not installed")
            elif not self.api_key:
                print("⚠️  Claude Brain disabled: ANTHROPIC_API_KEY not found")
            return

        # Initialize Anthropic client
        self.client = Anthropic(api_key=self.api_key)

        print(f"🧠 Claude Brain initialized with model: {model}")

    def _load_api_key(self):
        """Load Anthropic API key from environment"""
        # Try Desktop/.env first
        desktop_env = os.path.join(os.path.expanduser("~"), "Desktop", ".env")
        if os.path.exists(desktop_env):
            load_dotenv(desktop_env)

        # Also try current directory .env
        load_dotenv()

        self.api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")

    def understand(self, natural_request: str) -> ClaudeIntent:
        """
        Understand natural language request using Claude

        Args:
            natural_request: Natural language from user (e.g., "what changed today?")

        Returns:
            ClaudeIntent with commands to execute
        """
        if not self.enabled:
            # Fallback: return empty intent
            return ClaudeIntent(
                understood=False,
                commands=[],
                reasoning="Claude Brain not available",
                confidence=0.0,
                natural_request=natural_request
            )

        try:
            # Create system prompt
            system_prompt = self._build_system_prompt()

            # Ask Claude to understand the intent
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"User said: \"{natural_request}\"\n\nWhat commands should I execute? Respond in JSON format."
                }]
            )

            # Parse response
            response_text = response.content[0].text

            # Try to extract JSON
            intent_data = self._extract_json(response_text)

            if intent_data:
                return ClaudeIntent(
                    understood=intent_data.get("understood", True),
                    commands=intent_data.get("commands", []),
                    reasoning=intent_data.get("reasoning", ""),
                    confidence=intent_data.get("confidence", 0.9),
                    natural_request=natural_request
                )
            else:
                # Fallback parsing
                return self._fallback_parse(natural_request, response_text)

        except Exception as e:
            print(f"❌ Claude Brain error: {e}")
            return ClaudeIntent(
                understood=False,
                commands=[],
                reasoning=f"Error: {e}",
                confidence=0.0,
                natural_request=natural_request
            )

    def _build_system_prompt(self) -> str:
        """Build system prompt for Claude"""
        return """You are the Claude Brain of CORE_X_AGENT - an AI runtime system with voice control.

Your job: Understand natural language requests and convert them to executable commands.

AVAILABLE COMMANDS (git operations via LAB_DEV module):
1. "show git status" - Show working tree status
2. "show git diff [file]" - Show changes in files
3. "show git log" or "show last N commits" - Show commit history
4. "list branches" or "show branches" - List git branches
5. "show git stash" - Show stashed changes
6. "commit changes" - Commit changes (requires confirmation)
7. "push to remote" - Push commits (requires confirmation)
8. "pull from remote" - Pull commits
9. "create branch NAME" - Create new branch
10. "switch to branch NAME" - Switch branches

EXAMPLES:

User: "what changed in my code today?"
Response: {
  "understood": true,
  "commands": ["show git status", "show git diff"],
  "reasoning": "User wants to see recent changes - show status and diff",
  "confidence": 0.95
}

User: "show me the last 5 commits"
Response: {
  "understood": true,
  "commands": ["show last 5 commits"],
  "reasoning": "User wants commit history",
  "confidence": 1.0
}

User: "what's the weather?"
Response: {
  "understood": false,
  "commands": [],
  "reasoning": "This is not a git/code operation - CORE_X_AGENT only handles git operations currently",
  "confidence": 1.0
}

User: "list my branches and show status"
Response: {
  "understood": true,
  "commands": ["list branches", "show git status"],
  "reasoning": "User wants multiple operations - both branch list and status",
  "confidence": 0.9
}

RESPOND IN JSON FORMAT ONLY. Be intelligent about understanding intent."""

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from Claude's response"""
        try:
            # Try to find JSON in text
            start = text.find("{")
            end = text.rfind("}") + 1

            if start >= 0 and end > start:
                json_text = text[start:end]
                return json.loads(json_text)

            return None
        except:
            return None

    def _fallback_parse(self, request: str, response_text: str) -> ClaudeIntent:
        """Fallback parsing if JSON extraction fails"""
        # Simple heuristic: look for command-like text
        commands = []

        if "git status" in response_text.lower():
            commands.append("show git status")
        if "git diff" in response_text.lower():
            commands.append("show git diff")
        if "git log" in response_text.lower() or "commits" in response_text.lower():
            commands.append("show git log")

        return ClaudeIntent(
            understood=len(commands) > 0,
            commands=commands,
            reasoning=response_text[:200],
            confidence=0.5,
            natural_request=request
        )

    def format_response(
        self,
        natural_request: str,
        commands_executed: List[str],
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Format natural language response using Claude

        Args:
            natural_request: Original user request
            commands_executed: Commands that were executed
            results: Results from each command

        Returns:
            Natural language response
        """
        if not self.enabled:
            return "Claude Brain not available for response formatting."

        try:
            # Build context
            context = f"User asked: \"{natural_request}\"\n\n"
            context += "Commands executed:\n"

            for i, (cmd, result) in enumerate(zip(commands_executed, results)):
                context += f"{i+1}. {cmd}\n"
                context += f"   Result: {json.dumps(result, indent=2)[:500]}\n"

            # Ask Claude to format response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system="You are Claude Brain. Format command results into natural, conversational responses. Be concise and friendly. Speak in second person (you, your). Focus on what matters to the user.",
                messages=[{
                    "role": "user",
                    "content": f"{context}\n\nProvide a natural, conversational response to the user."
                }]
            )

            return response.content[0].text.strip()

        except Exception as e:
            print(f"❌ Response formatting error: {e}")
            return f"Executed {len(commands_executed)} command(s). Check results above."


# Convenience functions
_default_brain: Optional[ClaudeBrain] = None

def get_claude_brain() -> ClaudeBrain:
    """Get or create default Claude Brain singleton"""
    global _default_brain
    if _default_brain is None:
        _default_brain = ClaudeBrain()
    return _default_brain


# Example usage
if __name__ == "__main__":
    print("🧠 CORE_X_AGENT - Claude Brain Module\n")
    print("=" * 60)

    brain = ClaudeBrain()

    print(f"\nClaude Brain enabled: {brain.enabled}")
    print(f"API key loaded: {brain.api_key is not None}")

    if not brain.enabled:
        print("\n⚠️  To enable Claude Brain:")
        print("1. pip install anthropic")
        print("2. Add to Desktop/.env:")
        print("   ANTHROPIC_API_KEY=your_key_here")
        sys.exit(0)

    print("\n🎯 Testing Claude Brain...\n")

    # Test cases
    test_requests = [
        "what changed in my code?",
        "show me the last 5 commits",
        "list all branches",
        "what's the weather?",  # Should understand it's not supported
    ]

    for request in test_requests:
        print(f"\n📝 Request: {request}")
        intent = brain.understand(request)

        print(f"   Understood: {intent.understood}")
        print(f"   Commands: {intent.commands}")
        print(f"   Reasoning: {intent.reasoning}")
        print(f"   Confidence: {intent.confidence}")

    print("\n" + "=" * 60)
    print("✅ Claude Brain test complete!")
