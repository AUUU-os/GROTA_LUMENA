"""
Error Message Formatter
Converts technical errors into user-friendly, actionable messages
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ErrorCategory(Enum):
    """Categories of errors"""
    POLICY_DENIED = "policy_denied"
    COMMAND_UNKNOWN = "command_unknown"
    MODULE_ERROR = "module_error"
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"


@dataclass
class EnhancedError:
    """Enhanced error message with context and suggestions"""
    category: ErrorCategory
    title: str
    message: str
    technical_details: Optional[str] = None
    suggestions: List[str] = None
    docs_link: Optional[str] = None

    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "technical_details": self.technical_details,
            "suggestions": self.suggestions,
            "docs_link": self.docs_link
        }


class ErrorFormatter:
    """
    Formats technical errors into user-friendly messages

    Example:
        formatter = ErrorFormatter()
        error = formatter.format_policy_denial(
            operation="git_commit",
            mode="talk",
            reason="Operation denied in TALK mode"
        )
        # Returns EnhancedError with helpful message and suggestions
    """

    def __init__(self):
        self.git_error_patterns = self._build_git_error_patterns()

    def _build_git_error_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build patterns for common git errors"""
        return {
            "nothing to commit": {
                "title": "No Changes to Commit",
                "message": "Your working tree is clean - there are no changes to commit.",
                "suggestions": [
                    "Make some changes to your files first",
                    "Use 'git status' to check for unstaged changes",
                    "Use 'git diff' to see what would be committed"
                ]
            },
            "not a git repository": {
                "title": "Not a Git Repository",
                "message": "The current directory is not initialized as a git repository.",
                "suggestions": [
                    "Run 'git init' to create a new repository",
                    "Navigate to a directory that contains a .git folder",
                    "Clone an existing repository with 'git clone'"
                ]
            },
            "permission denied": {
                "title": "Permission Denied",
                "message": "You don't have permission to perform this git operation.",
                "suggestions": [
                    "Check your SSH key configuration",
                    "Verify you have write access to the repository",
                    "Try using HTTPS authentication instead of SSH"
                ]
            },
            "fatal: no remote": {
                "title": "No Remote Repository",
                "message": "No remote repository is configured for push/pull operations.",
                "suggestions": [
                    "Add a remote: 'git remote add origin <url>'",
                    "Check existing remotes: 'git remote -v'",
                    "Verify the remote URL is correct"
                ]
            },
            "conflict": {
                "title": "Merge Conflict",
                "message": "Git detected conflicting changes that need to be resolved manually.",
                "suggestions": [
                    "Open the conflicting files and resolve merge markers",
                    "Use 'git status' to see which files have conflicts",
                    "After resolving, stage the files with 'git add'",
                    "Complete the merge with 'git commit'"
                ]
            },
            "branch already exists": {
                "title": "Branch Already Exists",
                "message": "A branch with this name already exists.",
                "suggestions": [
                    "Choose a different branch name",
                    "Switch to the existing branch: 'git checkout <branch>'",
                    "Delete the old branch first: 'git branch -d <branch>'"
                ]
            }
        }

    def format_policy_denial(
        self,
        operation: str,
        mode: str,
        reason: str,
        module: str = None
    ) -> EnhancedError:
        """
        Format policy denial errors with helpful context

        Args:
            operation: The denied operation (e.g., "git_commit")
            mode: Current window mode (talk/design/exec)
            reason: Technical denial reason
            module: Module name (e.g., "lab_dev")

        Returns:
            EnhancedError with user-friendly message
        """
        mode_upper = mode.upper()

        # Build user-friendly title
        title = f"Operation Denied in {mode_upper} Mode"

        # Build detailed message based on mode
        if mode == "talk":
            message = (
                f"The operation '{operation}' cannot be executed in TALK mode. "
                f"TALK mode is for safe conversation only - no system operations are allowed."
            )
            suggestions = [
                "Switch to DESIGN mode for controlled execution: 'corex mode design'",
                "Switch to EXEC mode for full execution: 'corex mode exec'",
                "Ask questions about what you want to do instead of executing"
            ]
        elif mode == "design":
            message = (
                f"The operation '{operation}' requires user confirmation in DESIGN mode. "
                f"DESIGN mode allows only whitelisted safe operations automatically."
            )
            suggestions = [
                "Approve this specific operation when prompted",
                "Switch to EXEC mode to allow all operations: 'corex mode exec'",
                f"Add '{operation}' to whitelist if you trust it"
            ]
        else:  # exec or other
            message = (
                f"The operation '{operation}' was denied. "
                f"This may be a blacklisted dangerous operation."
            )
            suggestions = [
                "Review the operation parameters for safety",
                "Check if this operation is on the blacklist",
                "Contact system administrator if you believe this should be allowed"
            ]

        # Add operation-specific suggestions
        if "commit" in operation:
            suggestions.append("Tip: Use 'git status' first to review what will be committed")
        elif "push" in operation:
            suggestions.append("Tip: Use 'git log' to review commits before pushing")
        elif "delete" in operation or "rm" in operation:
            suggestions.insert(0, "WARNING: This is a destructive operation that cannot be undone")

        return EnhancedError(
            category=ErrorCategory.POLICY_DENIED,
            title=title,
            message=message,
            technical_details=f"Policy reason: {reason}",
            suggestions=suggestions,
            docs_link="https://github.com/yourusername/core-x-agent#security-modes"
        )

    def format_command_unknown(
        self,
        command: str,
        similar_commands: List[str] = None
    ) -> EnhancedError:
        """
        Format unknown command errors with suggestions

        Args:
            command: The unrecognized command
            similar_commands: List of similar valid commands

        Returns:
            EnhancedError with suggestions
        """
        title = "Command Not Recognized"
        message = f"I couldn't understand the command: '{command}'"

        suggestions = [
            "Try rephrasing your command more explicitly",
            "Examples: 'show git status', 'commit my changes', 'list branches'",
            "Use 'corex --help' to see available commands"
        ]

        # Add similar commands if provided
        if similar_commands:
            suggestions.insert(0, f"Did you mean: {', '.join(similar_commands)}?")

        return EnhancedError(
            category=ErrorCategory.COMMAND_UNKNOWN,
            title=title,
            message=message,
            suggestions=suggestions,
            docs_link="https://github.com/yourusername/core-x-agent#command-examples"
        )

    def format_git_error(
        self,
        error_message: str,
        operation: str = None
    ) -> EnhancedError:
        """
        Format git command errors with helpful suggestions

        Args:
            error_message: Raw git error message
            operation: Git operation that failed (e.g., "git_commit")

        Returns:
            EnhancedError with context-specific help
        """
        error_lower = error_message.lower()

        # Try to match against known patterns
        for pattern, info in self.git_error_patterns.items():
            if pattern in error_lower:
                return EnhancedError(
                    category=ErrorCategory.MODULE_ERROR,
                    title=info["title"],
                    message=info["message"],
                    technical_details=f"Git error: {error_message}",
                    suggestions=info["suggestions"],
                    docs_link="https://github.com/yourusername/core-x-agent#git-operations"
                )

        # Generic git error if no pattern matches
        title = "Git Operation Failed"
        message = "The git operation encountered an error."
        suggestions = [
            "Check the technical details below for specifics",
            "Verify your git repository is in a valid state",
            "Use 'git status' to check repository status",
            "Review git documentation for this operation"
        ]

        if operation:
            suggestions.insert(0, f"The '{operation}' operation failed")

        return EnhancedError(
            category=ErrorCategory.MODULE_ERROR,
            title=title,
            message=message,
            technical_details=error_message,
            suggestions=suggestions
        )

    def format_validation_error(
        self,
        field: str,
        value: Any,
        constraint: str
    ) -> EnhancedError:
        """
        Format validation errors

        Args:
            field: Field that failed validation
            value: The invalid value
            constraint: Validation constraint that was violated

        Returns:
            EnhancedError with validation help
        """
        title = f"Invalid {field.title()}"
        message = f"The value '{value}' for {field} is invalid."

        suggestions = [
            f"Constraint: {constraint}",
            "Check the command syntax and try again",
            "Use 'corex --help' for valid parameter formats"
        ]

        # Field-specific suggestions
        if "branch" in field.lower():
            suggestions.append("Branch names can only contain letters, numbers, -, /, and _")
        elif "message" in field.lower():
            suggestions.append("Commit messages should be descriptive but concise")

        return EnhancedError(
            category=ErrorCategory.VALIDATION_ERROR,
            title=title,
            message=message,
            technical_details=f"{field}='{value}' violates: {constraint}",
            suggestions=suggestions
        )

    def format_system_error(
        self,
        error: Exception,
        context: str = None
    ) -> EnhancedError:
        """
        Format unexpected system errors

        Args:
            error: The exception that occurred
            context: Context where error occurred

        Returns:
            EnhancedError with troubleshooting steps
        """
        title = "System Error"
        message = "An unexpected error occurred in CORE_X_AGENT."

        suggestions = [
            "Check the technical details below",
            "Verify all dependencies are installed",
            "Check system logs for more information",
            "Report this issue if it persists"
        ]

        if context:
            message += f" Context: {context}"

        return EnhancedError(
            category=ErrorCategory.SYSTEM_ERROR,
            title=title,
            message=message,
            technical_details=f"{type(error).__name__}: {str(error)}",
            suggestions=suggestions,
            docs_link="https://github.com/yourusername/core-x-agent/issues"
        )


# Example usage and tests
if __name__ == "__main__":
    formatter = ErrorFormatter()

    # Test policy denial
    print("=== Policy Denial Test ===")
    error = formatter.format_policy_denial(
        operation="git_commit",
        mode="talk",
        reason="Operation denied in TALK mode"
    )
    print(f"Title: {error.title}")
    print(f"Message: {error.message}")
    print(f"Suggestions:")
    for s in error.suggestions:
        print(f"  - {s}")
    print()

    # Test git error
    print("=== Git Error Test ===")
    error = formatter.format_git_error(
        error_message="fatal: nothing to commit, working tree clean",
        operation="git_commit"
    )
    print(f"Title: {error.title}")
    print(f"Message: {error.message}")
    print(f"Suggestions:")
    for s in error.suggestions:
        print(f"  - {s}")
    print()

    # Test unknown command
    print("=== Unknown Command Test ===")
    error = formatter.format_command_unknown(
        command="do the thing",
        similar_commands=["commit", "push", "status"]
    )
    print(f"Title: {error.title}")
    print(f"Message: {error.message}")
    print(f"Suggestions:")
    for s in error.suggestions:
        print(f"  - {s}")
