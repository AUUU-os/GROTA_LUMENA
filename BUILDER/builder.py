"""
Builder — Central Orchestrator for GROTA LUMENA.

Entry point: starts the FastAPI daemon on port 8800.
Usage: python -m BUILDER.builder
"""

import sys
import os
import json
import logging
import socket
import time
from pathlib import Path
from datetime import datetime

# Ensure GROTA_LUMENA root is on path
grota_root = Path(__file__).resolve().parent.parent
if str(grota_root) not in sys.path:
    sys.path.insert(0, str(grota_root))

# Fix Windows UTF-8
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

from BUILDER.config import (
    HOST, PORT, VERSION, GROTA_ROOT, M_AI_SELF_DIR,
    OLLAMA_URL, DATABASE_DIR, INBOX_DIR, LOGS_DIR, ROUTING_TABLE,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-7s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("builder")

# ============================================================================
#  BOOTLOADER — System Diagnostics & ASCII Banner
# ============================================================================

C_RESET = ""
C_GREEN = ""
C_RED = ""
C_YELLOW = ""
C_CYAN = ""
C_DIM = ""
C_BOLD = ""

# Enable ANSI colors on Windows 10+
if sys.platform == "win32":
    os.system("")  # enables ANSI escape sequences

C_RESET = "\033[0m"
C_GREEN = "\033[92m"
C_RED = "\033[91m"
C_YELLOW = "\033[93m"
C_CYAN = "\033[96m"
C_DIM = "\033[2m"
C_BOLD = "\033[1m"


def _ok(text: str) -> str:
    return f"{C_GREEN}[OK]{C_RESET} {text}"


def _fail(text: str) -> str:
    return f"{C_RED}[!!]{C_RESET} {text}"


def _warn(text: str) -> str:
    return f"{C_YELLOW}[??]{C_RESET} {text}"


def _info(text: str) -> str:
    return f"{C_CYAN}[..]{C_RESET} {text}"


def _check_ollama() -> tuple[bool, list[str]]:
    """Check if Ollama is reachable and get model list."""
    import urllib.request
    try:
        req = urllib.request.Request(f"{OLLAMA_URL}/api/tags")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            return True, models
    except Exception:
        return False, []


def _check_port(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def _scan_agents() -> list[dict]:
    """Scan M-AI-SELF for registered agents."""
    agents = []
    if not M_AI_SELF_DIR.exists():
        return agents
    for folder in sorted(M_AI_SELF_DIR.iterdir()):
        if not folder.is_dir():
            continue
        who = folder / "WHO_AM_I.md"
        state = folder / "STATE.log"
        if who.exists():
            # Extract model from WHO_AM_I.md
            model = "?"
            try:
                text = who.read_text(encoding="utf-8", errors="replace")
                for line in text.split("\n"):
                    if line.startswith("**Model:**"):
                        model = line.split("**Model:**")[1].strip()
                        break
            except Exception:
                pass
            agents.append({
                "name": folder.name,
                "has_state": state.exists(),
                "model": model,
            })
    return agents


def _get_last_checkpoint() -> str:
    """Find the most recent checkpoint/snapshot."""
    # Check STATE.log of CLAUDE_LUSTRO for last checkpoint
    state_file = M_AI_SELF_DIR / "CLAUDE_LUSTRO" / "STATE.log"
    if state_file.exists():
        try:
            text = state_file.read_text(encoding="utf-8", errors="replace")
            lines = text.strip().split("\n")
            for line in reversed(lines):
                if "CHECKPOINT" in line and "|" in line:
                    return line.strip().split("|")[0].strip()
        except Exception:
            pass
    return "N/A"


def _count_tasks() -> dict:
    """Count tasks by status from builder_tasks.json."""
    tasks_file = DATABASE_DIR / "builder_tasks.json"
    counts = {"pending": 0, "running": 0, "done": 0, "failed": 0, "total": 0}
    if tasks_file.exists():
        try:
            data = json.loads(tasks_file.read_text(encoding="utf-8"))
            tasks = data if isinstance(data, list) else data.get("tasks", [])
            counts["total"] = len(tasks)
            for t in tasks:
                s = t.get("status", "pending")
                if s in counts:
                    counts[s] += 1
        except Exception:
            pass
    return counts


def _count_inbox() -> int:
    """Count pending items in INBOX."""
    if not INBOX_DIR.exists():
        return 0
    return len([f for f in INBOX_DIR.glob("*.md") if f.is_file()])


def _disk_free_gb(path: str = "E:\\") -> float:
    """Get free disk space in GB."""
    try:
        import shutil
        usage = shutil.disk_usage(path)
        return usage.free / (1024 ** 3)
    except Exception:
        return -1


def bootloader():
    """Run system diagnostics and display ASCII boot screen."""
    boot_start = time.time()

    # ---- Gather data ----
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ollama_ok, models = _check_ollama()
    agents = _scan_agents()
    last_checkpoint = _get_last_checkpoint()
    tasks = _count_tasks()
    inbox_count = _count_inbox()
    port_busy = _check_port(PORT)
    disk_gb = _disk_free_gb()

    # Categorize agents
    nadzorcy = [a for a in agents if a["name"] in ("CLAUDE_LUSTRO", "GEMINI_ARCHITECT", "CODEX")]
    sztab = [a for a in agents if a["name"] in (
        "STROZ_SECURITY", "INZYNIER_PERF", "ARCHITEKT_UX", "TESTER_QA",
        "NAVIGATOR_RAG", "KOWAL_TOOLS", "KRONIKARZ_DOCS"
    )]
    other = [a for a in agents if a not in nadzorcy and a not in sztab and a["name"] != "SHAD"]

    # Categorize models
    local_models = [m for m in models if "cloud" not in m]
    cloud_models = [m for m in models if "cloud" in m]

    # Known projects
    projects = []
    proj_checks = [
        ("LUMEN CORE X", Path("E:/[repo]"), "v19.0", ":8000"),
        ("GROTA LUMENA", GROTA_ROOT, f"Builder v{VERSION}", f":{PORT}"),
        ("SHAD BUILDER", Path("E:/SHAD/shad_builder"), "API", ":8000"),
        ("SIDEBAR OMEGA", Path("E:/SHAD/lumen_extension"), "v1.4", "ext"),
        ("OpenClaw", Path("E:/[ PROJECTS ]/[ LOCAL ]/openclaw"), "fork", "-"),
    ]
    for name, path, ver, port in proj_checks:
        exists = path.exists()
        projects.append({"name": name, "path": str(path), "exists": exists, "version": ver, "port": port})

    boot_ms = int((time.time() - boot_start) * 1000)

    # ---- RENDER ----
    W = 66  # box width

    print()
    print(f"{C_CYAN}")
    print(r"       __        ___  ___  ___  _  _    __                          ")
    print(r"      / /  __ __/   |/   |/   || || |  / /                          ")
    print(r"     / /  / // / /| / /| / /| || || |_/ /                           ")
    print(r"    / /__/ // / ___ / ___ / ___|__   __/                            ")
    print(r"   /____/___/_/  |_/  |_/  |_/   |_|                               ")
    print(r"                                                                     ")
    print(r"   =========================================================        ")
    print(r"    GROTA LUMENA  //  BUILDER BOOTLOADER  //  WATAHA ONLINE          ")
    print(r"   =========================================================        ")
    print(f"{C_RESET}")

    # ---- SYSTEM INFO ----
    print(f"  {C_BOLD}SYSTEM{C_RESET}")
    print(f"  {'='*W}")
    print(f"  Builder:        v{VERSION}")
    print(f"  Boot time:      {now}")
    print(f"  Boot diag:      {boot_ms}ms")
    print(f"  Endpoint:       http://localhost:{PORT}")
    print(f"  Last checkpoint:{C_YELLOW} {last_checkpoint}{C_RESET}")
    if disk_gb >= 0:
        color = C_GREEN if disk_gb > 20 else C_YELLOW if disk_gb > 5 else C_RED
        print(f"  Disk free (E:): {color}{disk_gb:.1f} GB{C_RESET}")
    print()

    # ---- PORT CHECK ----
    if port_busy:
        print(f"  {_warn(f'Port {PORT} jest juz zajety! Builder moze nie wystartowac.')}")
        print()

    # ---- OLLAMA ----
    print(f"  {C_BOLD}OLLAMA{C_RESET}  {OLLAMA_URL}")
    print(f"  {'='*W}")
    if ollama_ok:
        print(f"  {_ok(f'Online  |  {len(models)} modeli')}")
        if local_models:
            print(f"  Lokalne:  {C_GREEN}{', '.join(local_models)}{C_RESET}")
        if cloud_models:
            print(f"  Cloud:    {C_CYAN}{', '.join(cloud_models)}{C_RESET}")
    else:
        print(f"  {_fail('Ollama OFFLINE - agenci Ollama nie beda dzialac!')}")
    print()

    # ---- AGENCI ----
    print(f"  {C_BOLD}AGENCI{C_RESET}  ({len(agents)} zarejestrowanych)")
    print(f"  {'='*W}")

    if nadzorcy:
        print(f"  {C_CYAN}NADZORCY:{C_RESET}")
        for a in nadzorcy:
            status = C_GREEN + "OK" + C_RESET if a["has_state"] else C_RED + "!!" + C_RESET
            print(f"    [{status}]  {a['name']:<22}")

    if sztab:
        print(f"  {C_YELLOW}SZTAB:{C_RESET}")
        for a in sztab:
            status = C_GREEN + "OK" + C_RESET if a["has_state"] else C_RED + "!!" + C_RESET
            model_str = f"{C_DIM}({a['model']}){C_RESET}" if a["model"] != "?" else ""
            print(f"    [{status}]  {a['name']:<22} {model_str}")

    if other:
        print(f"  {C_DIM}INNE:{C_RESET}")
        for a in other:
            print(f"    [..]  {a['name']}")

    # SHAD
    shad = next((a for a in agents if a["name"] == "SHAD"), None)
    if shad:
        print(f"  {C_BOLD}ZRODLO:{C_RESET}")
        print(f"    [>>]  SHAD  {C_DIM}(human, decyzje i wizja){C_RESET}")

    print()

    # ---- ROUTING ----
    route_count = len(ROUTING_TABLE)
    print(f"  {C_BOLD}ROUTING{C_RESET}  ({route_count} typow zadan)")
    print(f"  {'='*W}")
    # Show in two columns
    items = list(ROUTING_TABLE.items())
    mid = (len(items) + 1) // 2
    left = items[:mid]
    right = items[mid:]
    for i in range(mid):
        l_name, l_cfg = left[i]
        l_agent = l_cfg.get("agent", "?")[:14]
        line = f"  {l_name:<18} -> {l_agent:<14}"
        if i < len(right):
            r_name, r_cfg = right[i]
            r_agent = r_cfg.get("agent", "?")[:14]
            line += f"  |  {r_name:<18} -> {r_agent}"
        print(line)
    print()

    # ---- TASKS ----
    print(f"  {C_BOLD}TASKS{C_RESET}")
    print(f"  {'='*W}")
    t = tasks
    print(f"  Total: {t['total']}  |  "
          f"{C_YELLOW}Pending: {t['pending']}{C_RESET}  |  "
          f"{C_CYAN}Running: {t['running']}{C_RESET}  |  "
          f"{C_GREEN}Done: {t['done']}{C_RESET}  |  "
          f"{C_RED}Failed: {t['failed']}{C_RESET}")
    if inbox_count > 0:
        print(f"  INBOX: {C_YELLOW}{inbox_count} plikow czeka{C_RESET}")
    print()

    # ---- PROJEKTY ----
    print(f"  {C_BOLD}PROJEKTY{C_RESET}")
    print(f"  {'='*W}")
    for p in projects:
        if p["exists"]:
            status = f"{C_GREEN}FOUND{C_RESET}"
        else:
            status = f"{C_DIM}-----{C_RESET}"
        print(f"  [{status}]  {p['name']:<18} {p['version']:<16} {C_DIM}{p['port']}{C_RESET}")
    print()

    # ---- FOOTER ----
    print(f"  {C_CYAN}{'='*W}{C_RESET}")
    print(f"  {C_BOLD}  WATAHA GOTOWA  |  GROTA ZYJE  |  SYSTEM AKTYWNY{C_RESET}")
    print(f"  {C_CYAN}{'='*W}{C_RESET}")
    print()
    print(f"  {C_BOLD}AUUUUUUUUUUUUUUUUUUUUUUUU!{C_RESET}")
    print()


# ============================================================================
#  MAIN
# ============================================================================

def main():
    import uvicorn
    from BUILDER.api.app import create_app

    # Run bootloader diagnostics
    bootloader()

    # Create and start app
    app = create_app()

    logger.info(f"Starting Builder v{VERSION} on {HOST}:{PORT}")

    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
