# Changelog

All notable changes to Builder will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-02-09

### Added
- Initial Builder daemon with FastAPI on port 8800
- AgentRegistry — scans M-AI-SELF/ for agent info (WHO_AM_I.md, STATE.log)
- TaskManager — CRUD with JSON persistence (DATABASE/builder_tasks.json)
- Dispatcher — keyword-based task classification + routing table
- Ollama Bridge — async integration with localhost:11434
- Claude/Gemini/Codex Bridges — file-based via INBOX/
- FileWatcher — monitors INBOX/ and M-AI-SELF/ for changes
- AuditLog — operation logging to BUILDER/logs/
- REST API: /api/v1/tasks, /api/v1/agents, /api/v1/status, /api/v1/health
- WebSocket feed: /ws/feed for live updates
- Entry point: builder.py (uvicorn)
