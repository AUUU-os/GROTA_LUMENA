import subprocess
import logging
import os

logger = logging.getLogger("GIT-MANAGER")

class GitManager:
    \"\"\"
    LUMEN GIT CONTROL
    Handles versioning, commits, and branch management.
    \"\"\"
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _run_git(self, args: list):
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"Git Error: {e.stderr}")
            return None

    def commit_changes(self, message: str):
        \"\"\"Stages and commits changes.\"\"\"
        self._run_git(["add", "."])
        return self._run_git(["commit", "-m", message])

    def push(self, remote: str = "origin", branch: str = "main"):
        return self._run_git(["push", remote, branch])

    def get_status(self):
        return self._run_git(["status", "--short"])

git_manager = GitManager()
