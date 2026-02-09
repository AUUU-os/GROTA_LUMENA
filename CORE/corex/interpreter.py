"""
Command Interpreter
Converts natural language AI commands into structured intents
"""

import re
from typing import Dict, Any, List
from dataclasses import dataclass
from enum import Enum


class ModuleType(Enum):
    """Available LAB modules"""

    LAB_DEV = "lab_dev"
    LAB_FILES = "lab_files"
    LAB_NET = "lab_net"
    LAB_MEDIA = "lab_media"
    WOLF_ENGINE = "wolf_engine"
    SENTINEL = "sentinel"
    ARCHITECT = "architect"
    KNOWLEDGE = "knowledge"
    OPTIMIZER = "optimizer"


@dataclass
class Intent:
    """Structured intent from AI command"""

    module: str  # Which LAB module to use
    operation: str  # What operation to perform
    params: Dict[str, Any]  # Parameters for the operation
    confidence: float  # Confidence in interpretation (0.0-1.0)
    raw_command: str  # Original command from AI
    metadata: Dict[str, Any]  # Additional context


class CommandInterpreter:
    """
    Interprets natural language commands from AI

    Converts vague AI requests like:
      "commit my changes"
      "show me what files changed"
      "push to github"

    Into structured intents:
      {module: "lab_dev", operation: "git_commit", params: {...}}
      {module: "lab_dev", operation: "git_status", params: {...}}
      {module: "lab_dev", operation: "git_push", params: {...}}

    Example:
        interpreter = CommandInterpreter()
        intent = interpreter.parse("commit my code with message 'fix bug'")
        # Intent(module="lab_dev", operation="git_commit",
        #        params={"message": "fix bug"})
    """

    def __init__(self):
        self.patterns = self._build_patterns()
        # Pre-compile patterns for performance
        for p in self.patterns:
            p["compiled"] = re.compile(p["regex"], re.IGNORECASE)

    def _build_patterns(self) -> List[Dict[str, Any]]:
        """
        Build pattern matching rules for common commands

        Each pattern has:
        - regex: Regular expression to match command
        - module: Which LAB module handles it
        - operation: Operation name
        - param_extractor: Function to extract parameters
        """
        return [
            # ==================================================
            # SENTINEL COMMANDS
            # ==================================================
            {
                "regex": r"(?:security\s+)?scan(?:\s+(.+))?",
                "module": ModuleType.SENTINEL.value,
                "operation": "scan",
                "extract": lambda m: {
                    "path": m.group(1).strip() if m.group(1) else "."
                },
            },
            {
                "regex": r"security\s+status|sentinel\s+status",
                "module": ModuleType.SENTINEL.value,
                "operation": "status",
                "extract": lambda m: {},
            },
            {
                "regex": r"(?:show\s+)?(?:security\s+)?alerts",
                "module": ModuleType.SENTINEL.value,
                "operation": "alerts",
                "extract": lambda m: {},
            },
            {
                "regex": r"check\s+file\s+(?:safety\s+)?(.+)",
                "module": ModuleType.SENTINEL.value,
                "operation": "check_file",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # ==================================================
            # ARCHITECT COMMANDS
            # ==================================================
            {
                "regex": r"analyze\s+(?:file\s+)?(.+\.py)",
                "module": ModuleType.ARCHITECT.value,
                "operation": "analyze_file",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            {
                "regex": r"project\s+structure(?:\s+(.+))?",
                "module": ModuleType.ARCHITECT.value,
                "operation": "project_structure",
                "extract": lambda m: {
                    "path": m.group(1).strip() if m.group(1) else "."
                },
            },
            {
                "regex": r"find\s+imports?\s+(?:in\s+)?(.+)",
                "module": ModuleType.ARCHITECT.value,
                "operation": "find_imports",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            {
                "regex": r"(?:code\s+)?complexity\s+(?:of\s+)?(.+)",
                "module": ModuleType.ARCHITECT.value,
                "operation": "complexity",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # ==================================================
            # KNOWLEDGE COMMANDS
            # ==================================================
            {
                "regex": r"search\s+knowledge\s+(.+)",
                "module": ModuleType.KNOWLEDGE.value,
                "operation": "search",
                "extract": lambda m: {"query": m.group(1).strip()},
            },
            {
                "regex": r"ingest\s+(?:text\s+)?(.+)",
                "module": ModuleType.KNOWLEDGE.value,
                "operation": "ingest_text",
                "extract": lambda m: {"text": m.group(1).strip()},
            },
            {
                "regex": r"knowledge\s+stats",
                "module": ModuleType.KNOWLEDGE.value,
                "operation": "get_stats",
                "extract": lambda m: {},
            },
            # ==================================================
            # OPTIMIZER COMMANDS
            # ==================================================
            {
                "regex": r"profile\s+(.+\.py)",
                "module": ModuleType.OPTIMIZER.value,
                "operation": "profile",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            {
                "regex": r"(?:show\s+)?(?:system\s+)?resources",
                "module": ModuleType.OPTIMIZER.value,
                "operation": "resources",
                "extract": lambda m: {},
            },
            {
                "regex": r"optimize\s+(.+)",
                "module": ModuleType.OPTIMIZER.value,
                "operation": "suggestions",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # ==================================================
            # WOLF ENGINE COMMANDS
            # ==================================================
            {
                "regex": r"(?:generate|create|make)\s+(?:wolf\s+)?(?:content|script|video)(?:\s+with\s+(\d+)\s+scenes)?",
                "module": ModuleType.WOLF_ENGINE.value,
                "operation": "generate_content",
                "extract": lambda m: {
                    "num_scenes": int(m.group(1)) if m.group(1) else 3
                },
            },
            # Git commands (LAB_DEV)
            # NOTE: git_log must come BEFORE git_commit to match "commits" (plural)
            {
                "regex": r"(?:git\s+)?(?:show\s+)?log|(?:show\s+)?(?:me\s+)?(?:the\s+)?(?:last|recent)\s+(\d+)?\s*commit(?:s)?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_log",
                "extract": lambda m: {"limit": int(m.group(1)) if m.group(1) else 10},
            },
            {
                "regex": r"(?:git\s+)?commit(?:\s+(?:my|the)\s+)?(?:code|changes|files)?(?:\s+with\s+message\s+['\"](.+?)['\"])?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_commit",
                "extract": lambda m: {
                    "message": m.group(1) if m.group(1) else "Update"
                },
            },
            {
                "regex": r"(?:git\s+)?(?:list\s+)?branch(?:es)?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_branch",
                "extract": lambda m: {"action": "list"},
            },
            {
                "regex": r"(?:git\s+)?create\s+branch\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_branch",
                "extract": lambda m: {"action": "create", "branch": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?switch\s+(?:to\s+)?branch\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_branch",
                "extract": lambda m: {"action": "switch", "branch": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?stash(?:\s+(?:my\s+)?changes)?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_stash",
                "extract": lambda m: {"action": "save"},
            },
            {
                "regex": r"(?:git\s+)?list\s+stash(?:es)?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_stash",
                "extract": lambda m: {"action": "list"},
            },
            {
                "regex": r"(?:git\s+)?add\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_add",
                "extract": lambda m: {"files": [m.group(1)]},
            },
            {
                "regex": r"(?:git\s+)?(?:show\s+)?status|what\s+(?:files\s+)?changed",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_status",
                "extract": lambda m: {},
            },
            {
                "regex": r"(?:git\s+)?diff(?:\s+(.+))?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_diff",
                "extract": lambda m: {"file": m.group(1) if m.group(1) else None},
            },
            {
                "regex": r"(?:git\s+)?push(?:\s+to\s+)?(?:origin\s+)?(.+)?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_push",
                "extract": lambda m: {"branch": m.group(1) if m.group(1) else "main"},
            },
            {
                "regex": r"(?:git\s+)?pull(?:\s+from\s+)?(?:origin\s+)?(.+)?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_pull",
                "extract": lambda m: {"branch": m.group(1) if m.group(1) else "main"},
            },
            {
                "regex": r"(?:git\s+)?checkout\s+(?:-b\s+)?(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_checkout",
                "extract": lambda m: {
                    "branch": m.group(1),
                    "create": "-b" in m.group(0),
                },
            },
            {
                "regex": r"(?:git\s+)?merge\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_merge",
                "extract": lambda m: {"branch": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?(?:list\s+)?tags?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_tag",
                "extract": lambda m: {"action": "list"},
            },
            {
                "regex": r"(?:git\s+)?create\s+tag\s+(.+?)(?:\s+with\s+message\s+['\"](.+?)['\"])?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_tag",
                "extract": lambda m: {
                    "action": "create",
                    "tag": m.group(1),
                    "message": m.group(2) if m.group(2) else None,
                },
            },
            {
                "regex": r"(?:git\s+)?delete\s+tag\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_tag",
                "extract": lambda m: {"action": "delete", "tag": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?(?:list\s+)?remotes?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_remote",
                "extract": lambda m: {"action": "list"},
            },
            {
                "regex": r"(?:git\s+)?add\s+remote\s+(.+?)\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_remote",
                "extract": lambda m: {
                    "action": "add",
                    "remote": m.group(1),
                    "url": m.group(2),
                },
            },
            {
                "regex": r"(?:git\s+)?remove\s+remote\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_remote",
                "extract": lambda m: {"action": "remove", "remote": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?reset\s+--?(soft|mixed|hard)(?:\s+(.+))?",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_reset",
                "extract": lambda m: {
                    "mode": m.group(1),
                    "commit": m.group(2) if m.group(2) else "HEAD",
                },
            },
            {
                "regex": r"(?:git\s+)?show\s+(?:commit\s+)?(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_show",
                "extract": lambda m: {"commit": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?blame\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_blame",
                "extract": lambda m: {"file": m.group(1)},
            },
            {
                "regex": r"(?:git\s+)?cherry-?pick\s+(.+)",
                "module": ModuleType.LAB_DEV.value,
                "operation": "git_cherry_pick",
                "extract": lambda m: {"commit": m.group(1)},
            },
            # ==================================================
            # FILE COMMANDS (LAB_FILES)
            # ==================================================
            # FILE_READ
            {
                "regex": r"(?:show|read|cat|display)\s+(?:me\s+)?(?:the\s+)?(?:file\s+)?(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_read",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # FILE_LIST
            # Match "list files" without path (use current dir)
            {
                "regex": r"^(?:list|ls|show)\s+files?\s*$",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_list",
                "extract": lambda m: {"path": "."},
            },
            # Match "list files in [path]"
            {
                "regex": r"(?:list|ls|show)\s+files?\s+in\s+(?:the\s+)?(?:directory\s+)?(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_list",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # Match "what files are in [path]"
            {
                "regex": r"what\s+(?:files\s+)?(?:are\s+)?in\s+(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_list",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # FILE_INFO
            {
                "regex": r"(?:show\s+)?(?:file\s+)?info(?:\s+for)?\s+(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_info",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # FILE_WRITE
            {
                "regex": r"write\s+(.+?)\s+to\s+(?:file\s+)?(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_write",
                "extract": lambda m: {
                    "content": m.group(1).strip(),
                    "path": m.group(2).strip(),
                },
            },
            {
                "regex": r"create\s+(?:a\s+)?file\s+(?:called\s+)?(.+?)(?:\s+with\s+(.+))?",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_write",
                "extract": lambda m: {
                    "path": m.group(1).strip(),
                    "content": m.group(2).strip() if m.group(2) else "",
                },
            },
            # FILE_APPEND
            {
                "regex": r"append\s+(.+?)\s+to\s+(?:file\s+)?(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_append",
                "extract": lambda m: {
                    "content": m.group(1).strip(),
                    "path": m.group(2).strip(),
                },
            },
            # FILE_COPY
            {
                "regex": r"copy\s+(.+?)\s+to\s+(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_copy",
                "extract": lambda m: {
                    "source": m.group(1).strip(),
                    "destination": m.group(2).strip(),
                },
            },
            # FILE_MOVE
            {
                "regex": r"(?:move|rename)\s+(.+?)\s+to\s+(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_move",
                "extract": lambda m: {
                    "source": m.group(1).strip(),
                    "destination": m.group(2).strip(),
                },
            },
            # FILE_DELETE
            {
                "regex": r"(?:delete|remove|rm)\s+(?:file\s+)?(.+)",
                "module": ModuleType.LAB_FILES.value,
                "operation": "file_delete",
                "extract": lambda m: {"path": m.group(1).strip()},
            },
            # Network commands (LAB_NET) - for future
            # HTTP_GET
            {
                "regex": r"(?:http\s+)?(?:get|fetch)\s+(.+)",
                "module": ModuleType.LAB_NET.value,
                "operation": "http_get",
                "extract": lambda m: {"url": m.group(1).strip()},
            },
            # HTTP_POST
            {
                "regex": r"(?:http\s+)?post\s+(?:to\s+)?(.+?)(?:\s+with\s+data\s+(.+))?",
                "module": ModuleType.LAB_NET.value,
                "operation": "http_post",
                "extract": lambda m: {
                    "url": m.group(1).strip(),
                    "data": m.group(2).strip() if m.group(2) else None,
                },
            },
            # HTTP_PUT
            {
                "regex": r"(?:http\s+)?put\s+(?:to\s+)?(.+?)(?:\s+with\s+data\s+(.+))?",
                "module": ModuleType.LAB_NET.value,
                "operation": "http_put",
                "extract": lambda m: {
                    "url": m.group(1).strip(),
                    "data": m.group(2).strip() if m.group(2) else None,
                },
            },
            # HTTP_DELETE
            {
                "regex": r"(?:http\s+)?delete\s+(.+)",
                "module": ModuleType.LAB_NET.value,
                "operation": "http_delete",
                "extract": lambda m: {"url": m.group(1).strip()},
            },
            # DOWNLOAD_FILE
            {
                "regex": r"download\s+(.+?)\s+(?:to\s+)?(.+)",
                "module": ModuleType.LAB_NET.value,
                "operation": "download_file",
                "extract": lambda m: {
                    "url": m.group(1).strip(),
                    "destination": m.group(2).strip(),
                },
            },
            # API_TEST (alias for http_get with better naming)
            {
                "regex": r"(?:test\s+)?api\s+(.+)",
                "module": ModuleType.LAB_NET.value,
                "operation": "http_get",
                "extract": lambda m: {"url": m.group(1).strip()},
            },
            {
                "regex": r"(?:http\s+)?(?:get|fetch)\s+(.+)",
                "module": ModuleType.LAB_NET.value,
                "operation": "http_get",
                "extract": lambda m: {"url": m.group(1)},
            },
        ]

    def parse(self, command: str) -> Intent:
        """
        Parse natural language command into structured intent

        Args:
            command: Natural language command from AI

        Returns:
            Intent object with module, operation, params

        Raises:
            ValueError: If command cannot be interpreted
        """
        command = command.strip().lower()

        # Try to match against known patterns
        for pattern in self.patterns:
            match = pattern["compiled"].search(command)
            if match:
                params = pattern["extract"](match)
                return Intent(
                    module=pattern["module"],
                    operation=pattern["operation"],
                    params=params,
                    confidence=0.9,  # High confidence for pattern match
                    raw_command=command,
                    metadata={"match_type": "pattern"},
                )

        # Fallback: try to guess from keywords
        return self._fallback_parse(command)

    def _fallback_parse(self, command: str) -> Intent:
        """
        Fallback parser when no pattern matches

        Uses simple keyword matching with lower confidence
        """
        # Git-related keywords
        if any(word in command for word in ["commit", "committed", "committing"]):
            return Intent(
                module=ModuleType.LAB_DEV.value,
                operation="git_commit",
                params={"message": "Update"},
                confidence=0.6,
                raw_command=command,
                metadata={"match_type": "keyword_fallback"},
            )

        if any(word in command for word in ["status", "changed", "modified"]):
            return Intent(
                module=ModuleType.LAB_DEV.value,
                operation="git_status",
                params={},
                confidence=0.6,
                raw_command=command,
                metadata={"match_type": "keyword_fallback"},
            )

        if any(word in command for word in ["security", "sentinel", "threat"]):
            return Intent(
                module=ModuleType.SENTINEL.value,
                operation="status",
                params={},
                confidence=0.5,
                raw_command=command,
                metadata={"match_type": "keyword_fallback"},
            )

        if any(word in command for word in ["architect", "structure", "complexity"]):
            return Intent(
                module=ModuleType.ARCHITECT.value,
                operation="project_structure",
                params={"path": "."},
                confidence=0.5,
                raw_command=command,
                metadata={"match_type": "keyword_fallback"},
            )

        if any(word in command for word in ["knowledge", "search knowledge"]):
            return Intent(
                module=ModuleType.KNOWLEDGE.value,
                operation="get_stats",
                params={},
                confidence=0.5,
                raw_command=command,
                metadata={"match_type": "keyword_fallback"},
            )

        if any(word in command for word in ["optimize", "profile", "resources"]):
            return Intent(
                module=ModuleType.OPTIMIZER.value,
                operation="resources",
                params={},
                confidence=0.5,
                raw_command=command,
                metadata={"match_type": "keyword_fallback"},
            )

        # Raise error if we really can't interpret
        raise ValueError(f"Cannot interpret command: '{command}'")

    def suggest_corrections(self, command: str) -> List[str]:
        """
        Suggest possible corrections for ambiguous commands

        Returns:
            List of suggested command variations
        """
        suggestions = []

        if "commit" in command.lower():
            suggestions.extend(
                [
                    "commit my changes",
                    "commit with message 'your message here'",
                    "git commit",
                ]
            )

        if "push" in command.lower():
            suggestions.extend(["push to origin main", "git push", "push my code"])

        return suggestions

    def validate_params(self, intent: Intent) -> Dict[str, str]:
        """
        Validate intent parameters

        Returns:
            Dictionary of validation errors (empty if valid)
        """
        errors = {}

        if intent.operation == "git_commit":
            if not intent.params.get("message"):
                errors["message"] = "Commit message is required"

        if intent.operation == "git_push":
            branch = intent.params.get("branch")
            if branch and not re.match(r"^[a-zA-Z0-9_/-]+$", branch):
                errors["branch"] = "Invalid branch name"

        return errors


# Example usage and tests
if __name__ == "__main__":
    interpreter = CommandInterpreter()

    # Test cases
    test_commands = [
        "commit my changes",
        "commit with message 'fix critical bug'",
        "show status",
        "what files changed",
        "git diff main.py",
        "push to origin main",
        "git pull",
        "generate wolf script with 5 scenes",  # NEW TEST
    ]

    print("🧠 Command Interpreter Tests\n")
    for cmd in test_commands:
        try:
            intent = interpreter.parse(cmd)
            print(f"✅ '{cmd}'")
            print(f"   → Module: {intent.module}")
            print(f"   → Operation: {intent.operation}")
            print(f"   → Params: {intent.params}")
            print(f"   → Confidence: {intent.confidence}")
            print()
        except ValueError as e:
            print(f"❌ '{cmd}' - {e}\n")

    # Test validation
    print("\n🔍 Validation Tests\n")
    intent = Intent(
        module="lab_dev",
        operation="git_commit",
        params={},  # Missing message!
        confidence=0.9,
        raw_command="commit",
        metadata={},
    )
    errors = interpreter.validate_params(intent)
    if errors:
        print(f"Validation errors: {errors}")
