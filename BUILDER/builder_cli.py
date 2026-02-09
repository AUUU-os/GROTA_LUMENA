"""
Builder CLI — command-line interface for Builder API.

Usage:
    python -m BUILDER.builder_cli status
    python -m BUILDER.builder_cli health
    python -m BUILDER.builder_cli agents
    python -m BUILDER.builder_cli agent CLAUDE_LUSTRO
    python -m BUILDER.builder_cli tasks
    python -m BUILDER.builder_cli task <id>
    python -m BUILDER.builder_cli new "Title" "Description" [priority]
    python -m BUILDER.builder_cli dispatch <id>
    python -m BUILDER.builder_cli run "Title" "Description" [priority]   # new + dispatch in one
    python -m BUILDER.builder_cli logs [limit]
    python -m BUILDER.builder_cli routing
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE = "http://localhost:8800/api/v1"


def _get(path):
    try:
        req = urllib.request.Request(f"{BASE}{path}")
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"[ERROR] Builder nie odpowiada: {e}")
        print("       Uruchom: python -m BUILDER.builder")
        sys.exit(1)


def _post(path, data=None):
    try:
        body = json.dumps(data).encode() if data else None
        req = urllib.request.Request(
            f"{BASE}{path}",
            data=body,
            headers={"Content-Type": "application/json"} if body else {},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"[ERROR] Builder nie odpowiada: {e}")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        err = json.loads(e.read())
        print(f"[ERROR] {e.code}: {err.get('detail', err)}")
        sys.exit(1)


def cmd_status():
    s = _get("/status")
    print(f"Builder v{s['version']} | {s['status'].upper()} | uptime {int(s['uptime_seconds'])}s")
    print(f"Tasks: {s.get('tasks', {})}")
    a = s.get("agents", {})
    print(f"Agents: {a.get('total', 0)} total | {a.get('by_status', {})}")


def cmd_health():
    h = _get("/health")
    print(f"Builder:  {h['builder']}")
    print(f"Version:  {h['version']}")
    print(f"Ollama:   {h['ollama']} ({len(h['ollama_models'])} models)")
    print(f"Agents:   {h['agents_total']} total, {h['agents_active']} active")
    print(f"Tasks:    {h['tasks_pending']} pending, {h['tasks_running']} running")
    if h["ollama_models"]:
        print(f"Models:   {', '.join(h['ollama_models'])}")


def cmd_agents():
    data = _get("/agents")
    print(f"{'AGENT':<22} {'BRIDGE':<10} {'STATUS':<10} CAPABILITIES")
    print("-" * 70)
    for a in data["agents"]:
        caps = ", ".join(a["capabilities"])
        print(f"{a['name']:<22} {a['bridge_type']:<10} {a['status']:<10} {caps}")


def cmd_agent(name):
    try:
        req = urllib.request.Request(f"{BASE}/agents/{name}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            a = json.loads(resp.read())
    except urllib.error.HTTPError:
        print(f"Agent '{name}' nie znaleziony")
        return
    print(f"Name:         {a['name']}")
    print(f"Role:         {a['role']}")
    print(f"Bridge:       {a['bridge_type']}")
    print(f"Status:       {a['status']}")
    print(f"Capabilities: {', '.join(a['capabilities'])}")
    print(f"Last seen:    {a.get('last_seen', 'N/A')}")
    print(f"Current task: {a.get('current_task', 'none')}")


def cmd_tasks(status_filter=None):
    path = "/tasks"
    if status_filter:
        path += f"?status={status_filter}"
    data = _get(path)
    if not data:
        print("Brak taskow.")
        return
    print(f"{'ID':<14} {'STATUS':<10} {'PRIORITY':<10} {'AGENT':<18} TITLE")
    print("-" * 80)
    for t in data:
        agent = t.get("assigned_to") or "-"
        print(f"{t['id']:<14} {t['status']:<10} {t['priority']:<10} {agent:<18} {t['title'][:30]}")


def cmd_task(task_id):
    try:
        req = urllib.request.Request(f"{BASE}/tasks/{task_id}")
        with urllib.request.urlopen(req, timeout=10) as resp:
            t = json.loads(resp.read())
    except urllib.error.HTTPError:
        print(f"Task '{task_id}' nie znaleziony")
        return
    print(f"ID:          {t['id']}")
    print(f"Title:       {t['title']}")
    print(f"Status:      {t['status']}")
    print(f"Priority:    {t['priority']}")
    print(f"Agent:       {t.get('assigned_to', 'none')}")
    print(f"Type:        {t.get('task_type', 'N/A')}")
    print(f"Created:     {t['created_at']}")
    print(f"Updated:     {t['updated_at']}")
    if t.get("description"):
        print(f"Description: {t['description']}")
    if t.get("result"):
        print(f"\n--- RESULT ---")
        print(t["result"])
    if t.get("error"):
        print(f"\n--- ERROR ---")
        print(t["error"])


def cmd_new(title, description, priority="medium"):
    data = _post("/tasks", {"title": title, "description": description, "priority": priority})
    print(f"Task created: {data['id']}")
    print(f"  Title:    {data['title']}")
    print(f"  Priority: {data['priority']}")
    print(f"  Status:   {data['status']}")
    return data["id"]


def cmd_dispatch(task_id):
    print(f"Dispatching {task_id}...")
    data = _post(f"/tasks/{task_id}/dispatch")
    r = data["routing"]
    t = data["task"]
    print(f"  Type:   {r['task_type']}")
    print(f"  Agent:  {r['agent']}")
    print(f"  Bridge: {r['bridge']}")
    print(f"  Status: {t['status']}")
    if t.get("result"):
        print(f"\n--- RESULT ---")
        print(t["result"])
    elif r["bridge"] != "ollama":
        print(f"  (async — wynik pojawi sie w INBOX/)")


def cmd_run(title, description, priority="medium"):
    """Create + dispatch in one step."""
    task_id = cmd_new(title, description, priority)
    print()
    cmd_dispatch(task_id)


def cmd_logs(limit=30):
    data = _get(f"/logs?limit={limit}")
    for line in data["logs"]:
        print(line)


def cmd_routing():
    data = _get("/routing")
    print(f"{'TYPE':<16} {'AGENT':<22} {'BRIDGE':<10} MODEL")
    print("-" * 70)
    for name, r in data["routing_table"].items():
        model = r.get("model", "-")
        print(f"{name:<16} {r['agent']:<22} {r['bridge']:<10} {model}")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()

    if cmd == "status":
        cmd_status()
    elif cmd == "health":
        cmd_health()
    elif cmd == "agents":
        cmd_agents()
    elif cmd == "agent" and len(args) > 1:
        cmd_agent(args[1])
    elif cmd == "tasks":
        cmd_tasks(args[1] if len(args) > 1 else None)
    elif cmd == "task" and len(args) > 1:
        cmd_task(args[1])
    elif cmd == "new" and len(args) >= 3:
        cmd_new(args[1], args[2], args[3] if len(args) > 3 else "medium")
    elif cmd == "dispatch" and len(args) > 1:
        cmd_dispatch(args[1])
    elif cmd == "run" and len(args) >= 3:
        cmd_run(args[1], args[2], args[3] if len(args) > 3 else "medium")
    elif cmd == "logs":
        cmd_logs(int(args[1]) if len(args) > 1 else 30)
    elif cmd == "routing":
        cmd_routing()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
