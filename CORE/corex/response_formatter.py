"""
Response Formatter
Converts JSON results to natural language for voice output
"""

import sys
from typing import Dict, Any, List, Optional

# Fix Windows encoding for emoji/unicode
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass


class ResponseFormatter:
    """
    Formats structured command results into natural language

    Converts JSON like {"clean": True} into
    "Your working tree is clean, no changes detected"

    Example:
        formatter = ResponseFormatter()
        text = formatter.format(operation="git_status", result={...})
        # Returns: "Your working tree is clean"
    """

    def format(
        self,
        operation: str,
        result: Dict[str, Any],
        success: bool = True
    ) -> str:
        """
        Format result based on operation type

        Args:
            operation: Operation name (e.g., "git_status")
            result: Result dictionary from LAB module
            success: Whether operation succeeded

        Returns:
            Natural language description of result
        """
        if not success:
            return self._format_error(operation, result)

        # Route to specific formatter based on operation
        formatters = {
            "git_status": self._format_git_status,
            "git_diff": self._format_git_diff,
            "git_log": self._format_git_log,
            "git_commit": self._format_git_commit,
            "git_push": self._format_git_push,
            "git_pull": self._format_git_pull,
            "git_branch": self._format_git_branch,
            "git_stash": self._format_git_stash,
            "git_add": self._format_git_add,
        }

        formatter_func = formatters.get(operation)
        if formatter_func:
            return formatter_func(result)

        # Fallback: generic formatting
        return self._format_generic(operation, result)

    def _format_git_status(self, result: Dict[str, Any]) -> str:
        """Format git status result"""
        if result.get("clean", False):
            return "Your working tree is clean. No changes detected. Everything is committed."

        files = result.get("files", [])
        total = len(files)

        if total == 0:
            return "Your working tree is clean."

        # Count by status (git uses codes like "M ", "??", "A ", etc.)
        modified = sum(1 for f in files if f.get("status", "").strip().startswith(("M", "MM")))
        untracked = sum(1 for f in files if f.get("status", "").strip() == "??")
        staged = sum(1 for f in files if f.get("status", "").strip().startswith(("A", "AM")))

        parts = []
        if modified > 0:
            parts.append(f"{modified} modified file{'s' if modified > 1 else ''}")
        if untracked > 0:
            parts.append(f"{untracked} untracked file{'s' if untracked > 1 else ''}")
        if staged > 0:
            parts.append(f"{staged} staged file{'s' if staged > 1 else ''}")

        # If we couldn't categorize any, just say total
        if not parts:
            return f"You have {total} changed file{'s' if total > 1 else ''}."

        return f"You have {', '.join(parts)}. Total: {total} changed files."

    def _format_git_diff(self, result: Dict[str, Any]) -> str:
        """Format git diff result"""
        file = result.get("file", "")
        changes = result.get("changes", "")

        if not changes:
            return f"No changes in {file}." if file else "No changes detected."

        lines = changes.split("\n")
        added = sum(1 for line in lines if line.startswith("+"))
        removed = sum(1 for line in lines if line.startswith("-"))

        if file:
            return f"Changes in {file}: {added} lines added, {removed} lines removed."
        else:
            return f"Diff shows {added} lines added and {removed} lines removed."

    def _format_git_log(self, result: Dict[str, Any]) -> str:
        """Format git log result"""
        commits = result.get("commits", [])
        total = result.get("total", len(commits))

        if total == 0:
            return "No commits found in the log."

        # Build commit list
        commit_descriptions = []
        for i, commit in enumerate(commits[:5], 1):  # Limit to 5 for voice
            hash_short = commit.get("hash", "")[:7]
            message = commit.get("message", "No message").split("\n")[0]  # First line only
            author = commit.get("author", "Unknown")

            commit_descriptions.append(
                f"{i}. {message} by {author}"
            )

        commits_text = ". ".join(commit_descriptions)

        if total > 5:
            return f"Here are your last {total} commits. Showing the first 5: {commits_text}. Would you like me to read more?"
        else:
            return f"Here are your last {total} commit{'s' if total > 1 else ''}: {commits_text}."

    def _format_git_commit(self, result: Dict[str, Any]) -> str:
        """Format git commit result"""
        hash_val = result.get("hash", "")
        message = result.get("message", "")
        files_changed = result.get("files_changed", 0)

        hash_short = hash_val[:7] if hash_val else "unknown"

        return f"Commit successful! Hash {hash_short}. Message: {message}. {files_changed} file{'s' if files_changed != 1 else ''} changed."

    def _format_git_push(self, result: Dict[str, Any]) -> str:
        """Format git push result"""
        branch = result.get("branch", "main")
        commits_pushed = result.get("commits_pushed", 0)

        if commits_pushed > 0:
            return f"Successfully pushed {commits_pushed} commit{'s' if commits_pushed > 1 else ''} to {branch}."
        else:
            return f"Push to {branch} complete. Everything up to date."

    def _format_git_pull(self, result: Dict[str, Any]) -> str:
        """Format git pull result"""
        branch = result.get("branch", "main")
        commits_pulled = result.get("commits_pulled", 0)
        files_changed = result.get("files_changed", 0)

        if commits_pulled > 0:
            return f"Pulled {commits_pulled} commit{'s' if commits_pulled > 1 else ''} from {branch}. {files_changed} file{'s' if files_changed != 1 else ''} updated."
        else:
            return f"Pull from {branch} complete. Already up to date."

    def _format_git_branch(self, result: Dict[str, Any]) -> str:
        """Format git branch result"""
        action = result.get("action", "list")

        if action == "list":
            branches = result.get("branches", [])
            total = result.get("total", len(branches))

            if total == 0:
                return "No branches found."

            current = next((b["name"] for b in branches if b.get("current")), None)

            if total == 1:
                return f"You have 1 branch: {branches[0]['name']}, which is your current branch."

            branch_names = [b["name"] for b in branches]
            return f"You have {total} branches: {', '.join(branch_names)}. Current branch: {current}."

        elif action == "create":
            branch = result.get("branch", "")
            return f"Created new branch: {branch}."

        elif action == "switch":
            branch = result.get("branch", "")
            return f"Switched to branch: {branch}."

        elif action == "delete":
            branch = result.get("branch", "")
            return f"Deleted branch: {branch}."

        return "Branch operation complete."

    def _format_git_stash(self, result: Dict[str, Any]) -> str:
        """Format git stash result"""
        action = result.get("action", "save")

        if action == "save":
            return "Changes stashed successfully. Your working tree is now clean."

        elif action == "list":
            stashes = result.get("stashes", [])
            total = len(stashes)

            if total == 0:
                return "No stashes found."

            return f"You have {total} stash{'es' if total > 1 else ''} saved."

        elif action == "pop":
            return "Stash popped successfully. Changes restored to working tree."

        elif action == "apply":
            return "Stash applied successfully."

        return "Stash operation complete."

    def _format_git_add(self, result: Dict[str, Any]) -> str:
        """Format git add result"""
        files = result.get("files", [])
        total = len(files)

        if total == 0:
            return "No files added to staging area."

        if total == 1:
            return f"Added {files[0]} to staging area."

        return f"Added {total} files to staging area: {', '.join(files[:3])}{'...' if total > 3 else ''}."

    def _format_error(self, operation: str, error: Dict[str, Any]) -> str:
        """Format error message"""
        title = error.get("title", "Operation Failed")
        message = error.get("message", "An error occurred")
        suggestions = error.get("suggestions", [])

        # Start with error message
        text = f"{title}. {message}"

        # Add first suggestion if available
        if suggestions and len(suggestions) > 0:
            text += f" Suggestion: {suggestions[0]}"

        return text

    def _format_generic(self, operation: str, result: Dict[str, Any]) -> str:
        """Generic fallback formatter"""
        # Try to find meaningful data to speak
        if "status" in result:
            return f"{operation} complete. Status: {result['status']}."

        if "success" in result:
            success = result["success"]
            return f"{operation} {'succeeded' if success else 'failed'}."

        # Last resort: just say operation completed
        return f"{operation} operation complete."


# Convenience function
_default_formatter: Optional[ResponseFormatter] = None

def get_formatter() -> ResponseFormatter:
    """Get or create default formatter singleton"""
    global _default_formatter
    if _default_formatter is None:
        _default_formatter = ResponseFormatter()
    return _default_formatter


def format_response(operation: str, result: Dict[str, Any], success: bool = True) -> str:
    """
    Quick format function using default formatter

    Args:
        operation: Operation name
        result: Result dictionary
        success: Whether operation succeeded

    Returns:
        Natural language description
    """
    formatter = get_formatter()
    return formatter.format(operation, result, success)


# Example usage and tests
if __name__ == "__main__":
    print("🎯 Response Formatter Tests\n")

    formatter = ResponseFormatter()

    # Test git_status
    print("1. git_status (clean):")
    result = {"clean": True}
    text = formatter.format("git_status", result)
    print(f"   {text}\n")

    print("2. git_status (dirty):")
    result = {
        "clean": False,
        "files": [
            {"file": "main.py", "status": "modified"},
            {"file": "test.py", "status": "untracked"},
            {"file": "config.py", "status": "staged"}
        ]
    }
    text = formatter.format("git_status", result)
    print(f"   {text}\n")

    # Test git_log
    print("3. git_log:")
    result = {
        "commits": [
            {"hash": "abc123def456", "message": "Fix bug", "author": "SHAD"},
            {"hash": "def456abc789", "message": "Add feature", "author": "SHAD"},
            {"hash": "789abc123def", "message": "Update docs", "author": "SHAD"}
        ],
        "total": 3
    }
    text = formatter.format("git_log", result)
    print(f"   {text}\n")

    # Test git_branch
    print("4. git_branch (list):")
    result = {
        "action": "list",
        "branches": [
            {"name": "main", "current": True},
            {"name": "feature-voice", "current": False}
        ],
        "total": 2
    }
    text = formatter.format("git_branch", result)
    print(f"   {text}\n")

    # Test git_commit
    print("5. git_commit:")
    result = {
        "hash": "abc123def456",
        "message": "Add voice chat",
        "files_changed": 3
    }
    text = formatter.format("git_commit", result)
    print(f"   {text}\n")

    # Test error
    print("6. Error:")
    error = {
        "title": "Operation Denied",
        "message": "No execution allowed in TALK mode",
        "suggestions": ["Switch to DESIGN mode", "Switch to EXEC mode"]
    }
    text = formatter.format("git_commit", error, success=False)
    print(f"   {text}\n")

    print("✅ Response formatter tests complete!")
