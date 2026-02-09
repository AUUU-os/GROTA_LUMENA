# Repository Guidelines

## Project Structure & Module Organization
- `CORE/`: Python backend (FastAPI + agent loop + memory). Entry points live in `CORE/corex/`.
- `DASHBOARD/`: React + Vite UI (single-page app in `DASHBOARD/index.tsx`).
- `CONFIG/`: System configuration (`lumen.yaml`, `wolf_config.yaml`).
- `DATABASE/`: Local data (`lumen_core.db`, `memory.json`).
- `M-AI-SELF/`: Agent identities, state logs, and resonance protocol.
- `INBOX/`: Agent handoffs and reports.

## Build, Test, and Development Commands
**Backend (CORE):**
- `python CORE/corex/api_server.py` — run LUMEN Core API server on port 8000.
- `pip install -r CORE/requirements.txt` — install backend dependencies.

**Frontend (DASHBOARD):**
- `cd DASHBOARD && npm install` — install UI dependencies.
- `npm run dev` — start Vite dev server.
- `npm run build` — production build.

**Tests:**
- `pytest` (from `CORE/`) — run backend tests if present.

## Coding Style & Naming Conventions
- Python: PEP 8, explicit typing where practical, async/await for IO.
- TypeScript/React: functional components, hooks (`useState`, `useEffect`), `camelCase` for variables, `PascalCase` for components.
- File paths and module names match existing structure (`corex/*`, `api/routes/*`).

## Testing Guidelines
- Primary framework: `pytest` + `pytest-asyncio`.
- Prefer test names like `test_<feature>_<case>.py`.
- Keep smoke tests fast; heavy GPU/LLM checks should be optional.

## Commit & Pull Request Guidelines
- Commit subjects are short and action-focused; emojis are used in history (e.g., “🛡️ Add security protocol…”).
- PRs should include: purpose summary, key files touched, and any new endpoints/UX changes.
- If touching security or KEYS, document in `GROTA_LOG.md`.

## Security & Configuration Tips
- **Never** commit anything from `KEYS/`.
- Follow `GROTA_MASTER.md` rules: no rearranging without approval; log writes in `GROTA_LOG.md`.
- Use `CONFIG/` as the source of truth for runtime settings.
