# PROJECT INDEX (GROTA_LUMENA)
Updated: 2026-02-10 22:51

## Core Areas
- CORE: API, memory engine, swarm, daemon.
  - CORE/corex/api_server.py (API entry)
  - CORE/corex/daemon.py (daemon)
  - CORE/corex/swarm/ (routing + engine)
  - CORE/corex/memory_engine.py (memory)
- DASHBOARD: UI (Memory Vault, reports, tasks).
  - DASHBOARD/index.tsx (main UI)
- BUILDER: system builder, dispatcher, agent registry.
  - BUILDER/api/app.py (builder API)
  - BUILDER/core/dispatcher.py (routing)
  - BUILDER/core/agent_registry.py (agents)
- M-AI-SELF: agent profiles, protocols, identity.
  - M-AI-SELF/CODEX/WHO_AM_I.md
- APP: bootloader, scripts, launchers.
  - APP/bootloader.ps1
- INBOX: task queue + briefings.
  - INBOX/ROADMAP_NOW.md
  - INBOX/SYSTEM_CARD_GROTA.md
- CONFIG / MANIFESTS: configuration and manifests.

## Shared Directories
- DATABASE: data storage.
- artifacts / checkpoints / TEMP: working artifacts and snapshots.
- scripts: tooling scripts.
- KEYS: secrets (do not touch).

## Notes
- Projects outside these core dirs are not indexed (no README/AGENTS found).
