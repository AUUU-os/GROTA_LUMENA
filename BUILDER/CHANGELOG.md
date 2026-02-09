# Changelog

All notable changes to Builder will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.3.0] - 2026-02-09

### Added
- Result polling endpoint: POST /api/v1/tasks/{id}/poll — checks for async results from Claude/Gemini/Codex
- Task retry endpoint: POST /api/v1/tasks/{id}/retry — re-dispatch failed/done tasks
- Task cancel endpoint: POST /api/v1/tasks/{id}/cancel — cancel running/pending tasks
- Manual dispatch override: POST /api/v1/tasks/{id}/dispatch accepts optional body with agent/bridge/model override
- Codex bridge `check_result()` — supports both standard and legacy result file formats
- File archiving: completed task files auto-moved to INBOX/DONE/
- CLI commands: poll, retry, cancel, watch (live tail)
- CLI flags: --agent, --bridge, --model for dispatch and run commands
- DispatchRequest Pydantic model for typed dispatch overrides

### Changed
- dispatch_task endpoint accepts optional DispatchRequest body
- _on_inbox_file archives files to INBOX/DONE/ after auto-complete
- CLI main() uses flag extraction for --agent/--bridge/--model

## [0.2.0] - 2026-02-09

### Added
- Full dispatch loop: FileWatcher auto-pickup RESULT_*_FROM_*.md and CODEX_RESULT_*.md
- WebSocket broadcast on task create, dispatch, running, complete, failed events
- Builder CLI (builder_cli.py) — terminal interface for all Builder operations
  - Commands: status, health, agents, agent, tasks, task, new, dispatch, run, logs, routing
  - `run` command: create + dispatch in one step

### Changed
- _on_inbox_file now parses result files and auto-completes matching tasks
- Dispatch endpoints broadcast events to all connected WebSocket clients

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
