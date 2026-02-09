"""
Builder CLI — command-line interface for Builder API.

Usage:
    python -m BUILDER.builder_cli status
    python -m BUILDER.builder_cli health
    python -m BUILDER.builder_cli agents
    python -m BUILDER.builder_cli agent CLAUDE_LUSTRO
    python -m BUILDER.builder_cli tasks [status]
    python -m BUILDER.builder_cli task <id>
    python -m BUILDER.builder_cli new "Title" "Description" [priority]
    python -m BUILDER.builder_cli dispatch <id> [--agent AGENT] [--bridge BRIDGE] [--model MODEL]
    python -m BUILDER.builder_cli run "Title" "Description" [priority] [--agent AGENT]
    python -m BUILDER.builder_cli poll <id>                              # check async result
    python -m BUILDER.builder_cli retry <id>                             # retry failed task
    python -m BUILDER.builder_cli cancel <id>                            # cancel running task
    python -m BUILDER.builder_cli watch [interval]                       # live tail of task changes
    python -m BUILDER.builder_cli logs [limit]
    python -m BUILDER.builder_cli routing
"""

import sys
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

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


def cmd_dispatch(task_id, agent=None, bridge=None, model=None):
    print(f"Dispatching {task_id}...")
    body = {}
    if agent:
        body["agent"] = agent
    if bridge:
        body["bridge"] = bridge
    if model:
        body["model"] = model
    data = _post(f"/tasks/{task_id}/dispatch", body if body else None)
    r = data["routing"]
    t = data["task"]
    print(f"  Type:   {r['task_type']}")
    print(f"  Agent:  {r['agent']}")
    print(f"  Bridge: {r['bridge']}")
    if r.get("model"):
        print(f"  Model:  {r['model']}")
    print(f"  Status: {t['status']}")
    if t.get("result"):
        print(f"\n--- RESULT ---")
        print(t["result"])
    elif r["bridge"] != "ollama":
        print(f"  (async — wynik pojawi sie w INBOX/)")


def cmd_run(title, description, priority="medium", agent=None):
    """Create + dispatch in one step."""
    task_id = cmd_new(title, description, priority)
    print()
    cmd_dispatch(task_id, agent=agent)


def cmd_poll(task_id):
    """Poll for async task result."""
    data = _post(f"/tasks/{task_id}/poll")
    status = data.get("status", "unknown")
    print(f"  Status: {status}")
    if status == "done":
        print(f"\n--- RESULT ---")
        print(data.get("result", ""))
    elif status == "waiting":
        print(f"  Wynik jeszcze niedostepny. Sprobuj ponownie za chwile.")
    else:
        print(f"  {data.get('message', '')}")


def cmd_retry(task_id):
    """Retry a failed task."""
    print(f"Retrying {task_id}...")
    data = _post(f"/tasks/{task_id}/retry")
    r = data.get("routing", {})
    t = data.get("task", {})
    print(f"  Agent:  {r.get('agent', 'N/A')}")
    print(f"  Bridge: {r.get('bridge', 'N/A')}")
    print(f"  Status: {t.get('status', 'N/A')}")
    if t.get("result"):
        print(f"\n--- RESULT ---")
        print(t["result"])


def cmd_cancel(task_id):
    """Cancel a running task."""
    print(f"Cancelling {task_id}...")
    data = _post(f"/tasks/{task_id}/cancel")
    if data.get("cancelled"):
        print(f"  Task cancelled.")
    else:
        print(f"  Failed to cancel: {data}")


def cmd_watch(interval=5):
    """Live tail of task status changes."""
    import time
    seen = {}
    print(f"Watching tasks (co {interval}s, Ctrl+C aby przerwac)...")
    print("-" * 70)
    try:
        while True:
            data = _get("/tasks")
            for t in data:
                tid = t["id"]
                status = t["status"]
                key = f"{tid}:{status}"
                if key not in seen:
                    seen[key] = True
                    agent = t.get("assigned_to") or "-"
                    ts = datetime.now().strftime("%H:%M:%S")
                    print(f"[{ts}] {tid} | {status:<10} | {agent:<18} | {t['title'][:40]}")
                    if status == "done" and t.get("result"):
                        preview = t["result"][:100].replace("\n", " ")
                        print(f"         -> {preview}...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWatch zakonczony.")


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


def _extract_flag(args, flag):
    """Extract --flag VALUE from args list, returns (value, remaining_args)."""
    result = None
    remaining = []
    i = 0
    while i < len(args):
        if args[i] == flag and i + 1 < len(args):
            result = args[i + 1]
            i += 2
        else:
            remaining.append(args[i])
            i += 1
    return result, remaining


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return

    cmd = args[0].lower()
    rest = args[1:]

    if cmd == "status":
        cmd_status()
    elif cmd == "health":
        cmd_health()
    elif cmd == "agents":
        cmd_agents()
    elif cmd == "agent" and len(rest) > 0:
        cmd_agent(rest[0])
    elif cmd == "tasks":
        cmd_tasks(rest[0] if rest else None)
    elif cmd == "task" and len(rest) > 0:
        cmd_task(rest[0])
    elif cmd == "new" and len(rest) >= 2:
        cmd_new(rest[0], rest[1], rest[2] if len(rest) > 2 else "medium")
    elif cmd == "dispatch" and len(rest) > 0:
        agent, rest2 = _extract_flag(rest, "--agent")
        bridge, rest3 = _extract_flag(rest2, "--bridge")
        model, rest4 = _extract_flag(rest3, "--model")
        cmd_dispatch(rest4[0], agent=agent, bridge=bridge, model=model)
    elif cmd == "run" and len(rest) >= 2:
        agent, rest2 = _extract_flag(rest, "--agent")
        priority = rest2[2] if len(rest2) > 2 else "medium"
        cmd_run(rest2[0], rest2[1], priority, agent=agent)
    elif cmd == "poll" and len(rest) > 0:
        cmd_poll(rest[0])
    elif cmd == "retry" and len(rest) > 0:
        cmd_retry(rest[0])
    elif cmd == "cancel" and len(rest) > 0:
        cmd_cancel(rest[0])
    elif cmd == "watch":
        cmd_watch(int(rest[0]) if rest else 5)
    elif cmd == "logs":
        cmd_logs(int(rest[0]) if rest else 30)
    elif cmd == "routing":
        cmd_routing()
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
