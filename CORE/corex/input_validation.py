"""
LUMEN Input Validation Module
Provides validation and sanitization for user inputs
"""

import re
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates and sanitizes user inputs"""

    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r":(){ :|:& };:",  # Fork bomb
        r"\$\{IFS\}",  # IFS injection
        r"`[^`]*`",  # Command substitution
        r"\$\([^)]*\)",  # Command substitution $()
        r"[;&|]\s*rm",  # Command chaining with rm
        r">\s*/dev/\w+",  # Device redirection
        r"curl.*\|.*sh",  # Pipe to shell
        r"wget.*\|.*sh",
    ]

    # Allowed characters for file paths
    SAFE_PATH_PATTERN = re.compile(r"^[\w\-\.\/\\:@\s]+$")

    # Maximum lengths
    MAX_COMMAND_LENGTH = 1000
    MAX_PATH_LENGTH = 500
    MAX_INPUT_LENGTH = 10000

    @classmethod
    def validate_command(cls, command: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a command string

        Returns:
            Tuple of (is_valid, sanitized_command, error_message)
        """
        if not command or not isinstance(command, str):
            return False, "", "Command must be a non-empty string"

        # Check length
        if len(command) > cls.MAX_COMMAND_LENGTH:
            return False, "", f"Command too long (max {cls.MAX_COMMAND_LENGTH} chars)"

        # Strip whitespace
        sanitized = command.strip()

        # Check for dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            if re.search(pattern, sanitized, re.IGNORECASE):
                logger.warning(f"Dangerous pattern detected: {pattern}")
                return False, "", f"Command contains dangerous pattern: {pattern}"

        # Check for null bytes
        if "\x00" in sanitized:
            return False, "", "Command contains null bytes"

        return True, sanitized, None

    @classmethod
    def validate_path(cls, path: str) -> Tuple[bool, str, Optional[str]]:
        """
        Validate a file path

        Returns:
            Tuple of (is_valid, sanitized_path, error_message)
        """
        if not path or not isinstance(path, str):
            return False, "", "Path must be a non-empty string"

        # Check length
        if len(path) > cls.MAX_PATH_LENGTH:
            return False, "", f"Path too long (max {cls.MAX_PATH_LENGTH} chars)"

        # Strip whitespace
        sanitized = path.strip()

        # Check for path traversal
        if ".." in sanitized.split("/") or ".." in sanitized.split("\\"):
            logger.warning(f"Path traversal attempt: {sanitized}")
            return False, "", "Path traversal not allowed"

        # Check for null bytes
        if "\x00" in sanitized:
            return False, "", "Path contains null bytes"

        # Basic pattern check
        if not cls.SAFE_PATH_PATTERN.match(sanitized):
            logger.warning(f"Invalid path characters: {sanitized}")
            return False, "", "Path contains invalid characters"

        return True, sanitized, None

    @classmethod
    def validate_text_input(
        cls, text: str, min_length: int = 1, max_length: int = 10000
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Validate general text input

        Returns:
            Tuple of (is_valid, sanitized_text, error_message)
        """
        if not isinstance(text, str):
            return False, "", "Input must be a string"

        # Check length
        if len(text) < min_length:
            return False, "", f"Input too short (min {min_length} chars)"

        if len(text) > max_length:
            return False, "", f"Input too long (max {max_length} chars)"

        # Basic sanitization
        sanitized = text.strip()

        # Remove control characters except newlines and tabs
        sanitized = "".join(
            char
            for char in sanitized
            if char == "\n" or char == "\t" or (ord(char) >= 32 and ord(char) < 127)
        )

        return True, sanitized, None

    @classmethod
    def sanitize_shell_command(cls, command: str) -> str:
        """
        Sanitize a shell command by escaping dangerous characters
        """
        # List of characters to escape
        dangerous_chars = [
            ";",
            "&",
            "|",
            "`",
            "$",
            "(",
            ")",
            "<",
            ">",
            "{",
            "}",
            "[",
            "]",
        ]

        sanitized = command
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, f"\\{char}")

        return sanitized

    @classmethod
    def validate_api_token(cls, token: str) -> Tuple[bool, Optional[str]]:
        """
        Validate API token format
        """
        if not token or not isinstance(token, str):
            return False, "Token must be a non-empty string"

        # Basic token format checks
        if len(token) < 10:
            return False, "Token too short"

        if len(token) > 500:
            return False, "Token too long"

        # Check for common token prefixes
        valid_prefixes = ["sk-", "Bearer ", "ghp_", "AIza"]
        has_valid_prefix = any(token.startswith(prefix) for prefix in valid_prefixes)

        if not has_valid_prefix and not re.match(r"^[A-Za-z0-9_\-]+$", token):
            return False, "Invalid token format"

        return True, None


def validate_daemon_command(
    command: str, allowed_prefixes: Optional[List[str]] = None
) -> Tuple[bool, str, Optional[str]]:
    """
    High-level validation for daemon commands
    """
    validator = InputValidator()

    # Basic validation
    is_valid, sanitized, error = validator.validate_command(command)
    if not is_valid:
        return False, "", error

    # Check allowed prefixes if specified
    if allowed_prefixes:
        has_allowed_prefix = any(
            sanitized.startswith(prefix) for prefix in allowed_prefixes
        )
        if not has_allowed_prefix:
            return (
                False,
                "",
                f"Command must start with one of: {', '.join(allowed_prefixes)}",
            )

    return True, sanitized, None
