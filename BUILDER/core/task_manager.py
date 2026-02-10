"""
TaskManager — task queue with priorities, persistence to JSON.
"""

from __future__ import annotations

import json
import uuid
import logging
from pathlib import Path
from datetime import datetime

from BUILDER.config import TASKS_FILE, DATABASE_DIR

logger = logging.getLogger("builder.tasks")

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


class Task:
    def __init__(
        self,
        title: str,
        description: str,
        priority: str = "medium",
        id: str | None = None,
        status: str = "pending",
        assigned_to: str | None = None,
        created_at: str | None = None,
        updated_at: str | None = None,
        result: str | None = None,
        error: str | None = None,
        task_type: str | None = None,
        depends_on: list[str] | None = None,
    ):
        self.id = id or uuid.uuid4().hex[:12]
        self.title = title
        self.description = description
        self.status = status
        self.priority = priority
        self.assigned_to = assigned_to
        self.created_at = created_at or datetime.now().isoformat()
        self.updated_at = updated_at or self.created_at
        self.result = result
        self.error = error
        self.task_type = task_type
        self.depends_on: list[str] = depends_on if depends_on is not None else []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "result": self.result,
            "error": self.error,
            "task_type": self.task_type,
            "depends_on": self.depends_on,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        return cls(**data)

    def touch(self):
        self.updated_at = datetime.now().isoformat()


class TaskManager:
    def __init__(self, tasks_file: Path | None = None):
        self._file = tasks_file or TASKS_FILE
        self._tasks: dict[str, Task] = {}
        self._load()

    def _load(self):
        """Load tasks from JSON file."""
        if self._file.exists():
            try:
                data = json.loads(self._file.read_text(encoding="utf-8"))
                for item in data:
                    task = Task.from_dict(item)
                    self._tasks[task.id] = task
                logger.info(f"Loaded {len(self._tasks)} tasks from {self._file}")
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}")

    def _save(self):
        """Persist tasks to JSON file."""
        DATABASE_DIR.mkdir(parents=True, exist_ok=True)
        data = [t.to_dict() for t in self._tasks.values()]
        self._file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def create(self, title: str, description: str, priority: str = "medium") -> Task:
        task = Task(title=title, description=description, priority=priority)
        self._tasks[task.id] = task
        self._save()
        logger.info(f"Created task {task.id}: {title}")
        return task

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, status: str | None = None, agent: str | None = None, sort_by: str | None = None) -> list[Task]:
        results = list(self._tasks.values())
        if status:
            results = [t for t in results if t.status == status]
        if agent:
            results = [t for t in results if t.assigned_to == agent]
        if sort_by == "priority":
            return sorted(results, key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.created_at))
        return sorted(results, key=lambda t: t.created_at, reverse=True)

    def pending_queue(self) -> list[Task]:
        """Return pending tasks sorted by priority (critical first), then by created_at (oldest first).
        Only includes tasks whose dependencies are all satisfied (is_ready)."""
        pending = [t for t in self._tasks.values() if t.status == "pending" and self.is_ready(t.id)]
        return sorted(pending, key=lambda t: (PRIORITY_ORDER.get(t.priority, 99), t.created_at))

    def next_task(self) -> Task | None:
        """Return the highest priority pending task, or None if no pending tasks."""
        queue = self.pending_queue()
        return queue[0] if queue else None

    def assign(self, task_id: str, agent_name: str) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.assigned_to = agent_name
        task.status = "assigned"
        task.touch()
        self._save()
        logger.info(f"Assigned task {task_id} to {agent_name}")
        return task

    def update_status(self, task_id: str, status: str) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = status
        task.touch()
        self._save()
        return task

    def complete(self, task_id: str, result: str) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = "done"
        task.result = result
        task.touch()
        self._save()
        logger.info(f"Completed task {task_id}")
        return task

    def fail(self, task_id: str, error: str) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        task.status = "failed"
        task.error = error
        task.touch()
        self._save()
        logger.warning(f"Failed task {task_id}: {error}")
        return task

    def update(self, task_id: str, **kwargs) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)
        task.touch()
        self._save()
        return task

    def add_dependency(self, task_id: str, depends_on_id: str) -> bool:
        """Add a dependency: task_id depends on depends_on_id. Both must exist."""
        task = self._tasks.get(task_id)
        dep = self._tasks.get(depends_on_id)
        if not task or not dep:
            return False
        if depends_on_id not in task.depends_on:
            task.depends_on.append(depends_on_id)
            task.touch()
            self._save()
            logger.info(f"Task {task_id} now depends on {depends_on_id}")
        return True

    def is_ready(self, task_id: str) -> bool:
        """Return True if all dependencies of task_id are done."""
        task = self._tasks.get(task_id)
        if not task:
            return False
        for dep_id in task.depends_on:
            dep = self._tasks.get(dep_id)
            if not dep or dep.status != "done":
                return False
        return True

    def get_blocked(self) -> list[Task]:
        """Return tasks that have at least one unmet (not done) dependency."""
        blocked = []
        for task in self._tasks.values():
            if not task.depends_on:
                continue
            for dep_id in task.depends_on:
                dep = self._tasks.get(dep_id)
                if not dep or dep.status != "done":
                    blocked.append(task)
                    break
        return blocked

    def delete(self, task_id: str) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            self._save()
            logger.info(f"Deleted task {task_id}")
            return True
        return False

    def history(self, limit: int = 50) -> list[Task]:
        all_tasks = sorted(self._tasks.values(), key=lambda t: t.updated_at, reverse=True)
        return all_tasks[:limit]

    def stats(self) -> dict:
        statuses = {}
        for t in self._tasks.values():
            statuses[t.status] = statuses.get(t.status, 0) + 1
        return statuses

