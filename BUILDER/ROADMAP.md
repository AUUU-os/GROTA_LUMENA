# Builder — Roadmap

## Completed

### v0.1.0 — Fundament
- FastAPI daemon on port 8800
- AgentRegistry — scans M-AI-SELF/ for agents
- TaskManager — CRUD with JSON persistence
- Dispatcher — keyword-based classification + routing table
- Ollama/Claude/Gemini/Codex Bridges
- FileWatcher — monitors INBOX/ and M-AI-SELF/
- AuditLog — operation logging
- REST API + WebSocket feed

### v0.2.0 — Dispatch Loop & CLI
- FileWatcher auto-pickup RESULT files
- WebSocket broadcast on task lifecycle events
- Builder CLI — terminal interface for all operations
- `run` command: create + dispatch in one step

### v0.3.0 — Full Integration
- Result polling endpoint (poll async tasks)
- Task retry / cancel endpoints
- Manual dispatch override (--agent, --bridge, --model)
- File archiving to INBOX/DONE/
- CLI: poll, retry, cancel, watch commands

---

## Planned

### v0.4.0 — Smart Dispatcher
- [ ] Ollama-based intent classification (llama3.2:1b) as fallback when keyword matching is uncertain
- [ ] Availability check — dispatcher verifies agent is idle before routing
- [ ] Priority queue — critical tasks preempt low priority
- [ ] Task dependencies — task B waits for task A to complete
- [ ] Confidence scoring — dispatcher reports how sure it is about routing

### v0.5.0 — Agent Autonomy
- [ ] Auto-pull Ollama models if missing
- [ ] Scheduled tasks — cron-like repeating tasks (e.g. hourly health check)
- [ ] Task chaining — output of task A becomes input of task B (pipeline)
- [ ] Parallel dispatch — send same task to multiple agents, pick best result

### v0.6.0 — Dashboard Pro
- [ ] Task creation form in Dashboard UI
- [ ] Live streaming results via WebSocket
- [ ] Task history with filters and search
- [ ] Agent detail view with logs and performance stats
- [ ] Notification system (toast on task complete/fail)

### v0.7.0 — Security & Production
- [ ] API authentication (API key or token)
- [ ] Rate limiting on endpoints
- [ ] Metrics endpoint (task counts, latency, agent utilization)
- [ ] Auto-restart with watchdog process
- [ ] Structured logging (JSON format option)

### v1.0.0 — Wataha Full Power
- [ ] Multi-step workflows (orchestrate N agents sequentially)
- [ ] Feedback loop — agent reviews output of another agent
- [ ] Learning routing — Builder remembers what worked, adjusts routing weights
- [ ] Natural language dispatch — "zrob mi API do userow" → Builder figures out the rest
- [ ] Plugin system — drop-in new bridges without code changes
