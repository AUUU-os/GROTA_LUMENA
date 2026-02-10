"""
GROTA LUMENA -- Bootloader
Wyswietla status systemu przy starcie sesji.
Zbiera live dane z: git, Ollama, Builder API, filesystem.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

# -- Paths ---------------------------------------------------------------
ROOT = Path(__file__).resolve().parent
M_AI_SELF = ROOT / "M-AI-SELF"
INBOX = ROOT / "INBOX"
DATABASE = ROOT / "DATABASE"
BUILDER_VERSION = ROOT / "BUILDER" / "VERSION"

# -- Config ---------------------------------------------------------------
BUILDER_URL = "http://localhost:8800"
OLLAMA_URL = "http://localhost:11434"
DASHBOARD_URL = "http://localhost:3002"

# -- Colors (ANSI) -------------------------------------------------------
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"
BG = "\033[92m"  # bright green
BY = "\033[93m"  # bright yellow
BC = "\033[96m"  # bright cyan


def _http_get(url: str, timeout: float = 2.0) -> dict | None:
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())
    except Exception:
        return None


def _run(cmd: list[str], cwd: str | None = None) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd or str(ROOT), timeout=5)
        return r.stdout.strip()
    except Exception:
        return ""


# -- Data collectors ------------------------------------------------------

def get_git_info() -> dict:
    branch = _run(["git", "branch", "--show-current"])
    log_line = _run(["git", "log", "--oneline", "-1"])
    commit_count = _run(["git", "rev-list", "--count", "HEAD"])
    last_tag = _run(["git", "describe", "--tags", "--abbrev=0"])
    dirty = _run(["git", "status", "--porcelain", "-s"])
    return {
        "branch": branch or "?",
        "last_commit": log_line or "?",
        "total_commits": commit_count or "?",
        "last_tag": last_tag or "none",
        "dirty": len(dirty.splitlines()) if dirty else 0,
    }


def get_agents() -> list[dict]:
    data = _http_get(f"{BUILDER_URL}/api/v1/agents")
    if data and "agents" in data:
        return data["agents"]
    agents = []
    if M_AI_SELF.exists():
        for d in sorted(M_AI_SELF.iterdir()):
            if d.is_dir() and (d / "WHO_AM_I.md").exists():
                state = d / "STATE.log"
                mtime = datetime.fromtimestamp(state.stat().st_mtime).strftime("%m-%d %H:%M") if state.exists() else "?"
                agents.append({"name": d.name, "last_seen": mtime, "bridge_type": "?"})
    return agents


def get_builder_status() -> dict | None:
    return _http_get(f"{BUILDER_URL}/api/v1/status")


def get_builder_health() -> dict | None:
    return _http_get(f"{BUILDER_URL}/api/v1/health")


def get_ollama_models() -> list[str]:
    data = _http_get(f"{OLLAMA_URL}/api/tags")
    if data and "models" in data:
        return [m["name"] for m in data["models"]]
    return []


def get_inbox_count() -> int:
    if INBOX.exists():
        return len([f for f in INBOX.iterdir() if f.is_file() and f.suffix == ".md"])
    return 0


def get_tasks_summary() -> dict | None:
    data = _http_get(f"{BUILDER_URL}/api/v1/tasks")
    if data and "tasks" in data:
        tasks = data["tasks"]
        by_status = {}
        for t in tasks:
            s = t.get("status", "?")
            by_status[s] = by_status.get(s, 0) + 1
        return {"total": len(tasks), "by_status": by_status}
    return None


def get_builder_version() -> str:
    if BUILDER_VERSION.exists():
        return BUILDER_VERSION.read_text().strip()
    return "?"


# -- Rendering ------------------------------------------------------------

def dot(ok: bool) -> str:
    return f"{GREEN}[ON]{RESET}" if ok else f"{RED}[--]{RESET}"


def agent_dot(status: str) -> str:
    if status == "idle":
        return f"{GREEN}o{RESET}"
    elif status in ("running", "assigned"):
        return f"{YELLOW}*{RESET}"
    return f"{RED}x{RESET}"


def render():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    git = get_git_info()
    builder = get_builder_status()
    health = get_builder_health()
    agents = get_agents()
    models = get_ollama_models()
    inbox_count = get_inbox_count()
    tasks = get_tasks_summary()
    bver = get_builder_version()

    builder_ok = builder is not None
    ollama_ok = health is not None and health.get("ollama") == "online"
    dashboard_ok = _http_get(DASHBOARD_URL) is not None

    local_models = [m for m in models if "cloud" not in m]
    cloud_models = [m for m in models if "cloud" in m]

    nadzorcy = [a for a in agents if a.get("bridge_type") in ("claude", "gemini", "codex")]
    sztab = [a for a in agents if a.get("bridge_type") == "ollama"]
    human = [a for a in agents if a.get("bridge_type") == "human"]

    W = 66
    SEP = "=" * W
    LINE = "-" * W

    print()
    print(f"{BC}{BOLD}")
    print("        .---.  .---.   .---. .---. .---.")
    print("       /   __\\/  _  \\ /  _  \\  _  \\  _  \\")
    print("      |   |  _|  |_| ||  | | | |_| |  |_| |")
    print("      |   |_| |  _  /|  |_| |  ___/|  _  |")
    print("       \\_____||_| \\_\\ \\___/ |_|    |_| |_|")
    print(f"        {MAGENTA}L U M E N A{BC}  --  Przestrzen Rezonansu")
    print(f"{RESET}")
    print(f"  {DIM}{now}{RESET}")
    print()

    # -- Services --
    print(f"  {BOLD}{WHITE}{SEP}{RESET}")
    print(f"  {BOLD}{WHITE}  USLUGI{RESET}")
    print(f"  {WHITE}{LINE}{RESET}")

    uptime = ""
    if builder and "uptime_seconds" in builder:
        secs = int(builder["uptime_seconds"])
        h, m = divmod(secs // 60, 60)
        uptime = f" (uptime: {h}h{m:02d}m)" if h else f" (uptime: {m}m)"

    print(f"    {dot(builder_ok)} Builder     {CYAN}:8800{RESET}    v{bver}{uptime}")
    print(f"    {dot(ollama_ok)} Ollama      {CYAN}:11434{RESET}   {len(local_models)} local + {len(cloud_models)} cloud")
    print(f"    {dot(dashboard_ok)} Dashboard   {CYAN}:3002{RESET}")
    print()

    # -- Git --
    print(f"  {BOLD}{WHITE}  GIT{RESET}")
    print(f"  {WHITE}{LINE}{RESET}")
    dirty_str = f"  {YELLOW}({git['dirty']} uncommitted){RESET}" if git["dirty"] else f"  {GREEN}clean{RESET}"
    print(f"    branch:  {BG}{git['branch']}{RESET}{dirty_str}")
    print(f"    last:    {DIM}{git['last_commit']}{RESET}")
    print(f"    commits: {git['total_commits']}   tag: {git['last_tag']}")
    print()

    # -- Agents --
    print(f"  {BOLD}{WHITE}  WATAHA ({len(agents)} agentow){RESET}")
    print(f"  {WHITE}{LINE}{RESET}")

    if human:
        for a in human:
            print(f"    {BY}*{RESET} {BOLD}{a['name']:<22}{RESET} {DIM}[zrodlo]{RESET}")

    if nadzorcy:
        for a in nadzorcy:
            bridge = a.get("bridge_type", "?")
            status = a.get("status", "idle")
            print(f"    {agent_dot(status)} {a['name']:<22} {DIM}[{bridge}]{RESET}")

    if sztab:
        for a in sztab:
            status = a.get("status", "idle")
            print(f"    {agent_dot(status)} {a['name']:<22} {DIM}[ollama]{RESET}")
    print()

    # -- Models --
    print(f"  {BOLD}{WHITE}  MODELE OLLAMA{RESET}")
    print(f"  {WHITE}{LINE}{RESET}")
    for m in local_models:
        tag = ""
        if "qwen3" in m:
            tag = f" {CYAN}<- PRIMARY{RESET}"
        elif "coder" in m:
            tag = f" {BLUE}<- kod{RESET}"
        elif "deepseek" in m:
            tag = f" {MAGENTA}<- reasoning{RESET}"
        elif "phi4" in m:
            tag = f" {GREEN}<- szybki{RESET}"
        elif "lumen" in m:
            tag = f" {YELLOW}<- custom{RESET}"
        print(f"    {m:<30}{tag}")
    if cloud_models:
        print(f"    {DIM}+ {len(cloud_models)} cloud stubs{RESET}")
    print()

    # -- Tasks --
    if tasks:
        print(f"  {BOLD}{WHITE}  ZADANIA (Builder){RESET}")
        print(f"  {WHITE}{LINE}{RESET}")
        parts = []
        for st, count in sorted(tasks["by_status"].items()):
            if st == "done":
                parts.append(f"{GREEN}{count} done{RESET}")
            elif st == "pending":
                parts.append(f"{YELLOW}{count} pending{RESET}")
            elif st == "running":
                parts.append(f"{CYAN}{count} running{RESET}")
            elif st == "failed":
                parts.append(f"{RED}{count} failed{RESET}")
            else:
                parts.append(f"{count} {st}")
        print(f"    {' | '.join(parts)}  (total: {tasks['total']})")
        print()

    # -- INBOX --
    if inbox_count > 0:
        print(f"  {BOLD}{WHITE}  INBOX{RESET}")
        print(f"  {WHITE}{LINE}{RESET}")
        print(f"    {BY}{inbox_count}{RESET} wiadomosci w skrzynce")
        print()

    # -- Footer --
    print(f"  {WHITE}{SEP}{RESET}")
    print(f"  {DIM}  Quick commands:{RESET}")
    print(f"    {CYAN}python -m BUILDER.builder{RESET}         -- start Builder daemon")
    print(f"    {CYAN}python -m BUILDER.builder_cli{RESET}     -- interactive CLI")
    print(f"    {CYAN}python grota_boot.py{RESET}              -- ten ekran")
    print(f"    {CYAN}curl localhost:8800/api/v1/status{RESET} -- API status")
    print(f"  {WHITE}{SEP}{RESET}")
    print()
    print(f"  {MAGENTA}{BOLD}  AUUUUUUUUUUUUUUUUUUUUUUUUU!{RESET}")
    print()


if __name__ == "__main__":
    if sys.platform == "win32":
        os.system("")  # triggers VT100 mode
    render()
