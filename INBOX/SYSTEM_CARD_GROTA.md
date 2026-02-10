# WIZYTÓWKA SYSTEMU — GROTA_LUMENA
## Snapshot: 2026-02-09

**Cel:** Centrum dowodzenia Watahy + pamięć kolektywna + ekosystem agentów.

**Warstwy:**
- **CORE/** — backend (FastAPI, daemon, swarm, memory SQL+Chroma).
- **DASHBOARD/** — UI (React/Vite, Memory Vault, raporty).
- **M-AI-SELF/** — tożsamości agentów i protokoły.

**Kluczowe funkcje:**
- Memory: store/search/recent/stats/metrics + filters + pagination.
- Export: JSON/CSV + backup + cleanup + auto‑backup co 6h.
- RAG: pamięć wstrzykiwana do OpenAI bridge + agent factory.
- Swarm: smart routing + agent_role (codex/gemini/claude/nova/promyk).
- UI: Memory Vault, kolektywna pamięć toggle, raporty.

**Stan teraz:**
- Ollama: OFFLINE (brak listy modeli).
- Swarm: offline (zależny od Ollama).

**Najważniejsze pliki:**
- CORE/corex/memory_engine.py
- CORE/corex/api_server.py
- CORE/corex/swarm/*
- DASHBOARD/index.tsx
- GROTA_LOG.md

**Zasady:**
- KEYS/.env nietykalne.
- Loguj zmiany w GROTA_LOG.md.

