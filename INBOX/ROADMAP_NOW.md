# ROADMAP NOW (GROTA_LUMENA)
Updated: 2026-02-10 22:42

## Immediate Tasks (Priority + Owner)
- [P0][CLAUDE] TASK_51f981f17ef5_FOR_CLAUDE: security review auth module; output INBOX/RESULT_51f981f17ef5_FROM_CLAUDE.md. ETA: ASAP.
- [P1][SWARM] TASK_SWARM_E2E: run swarm end-to-end; verify /api/v1/swarm/health, /api/v1/swarm/routes, smart_dispatch metadata. ETA: same day.
- [P1][GEMINI] TASK_TEST_CLEANUP_GEMINI: pytest only project tests (avoid site-packages). ETA: same day.
- [P2][CODEX/GEMINI/CLAUDE] TASK_CARD_*: system card GROTA_LUMENA (max 15 lines: goal/arch/status/key files). ETA: next.

## Checklists
- PR checklist: summary, files touched, endpoints/UI changes, screenshots, KEYS/.env untouched, GROTA_LOG.md updated.
- CI checklist: pip requirements, pytest (CORE), npm install/build (DASHBOARD), api health check.

## Missing Tasks to Create
- TASK_AUTH_SECURITY_REVIEW.md (if CLAUDE handoff not active)
- TASK_SWARM_STARTUP.md (start Ollama + swarm + verify routes)
- TASK_PROJECT_INDEX.md (scan projects for README/AGENTS)

## Notes
- INBOX is the shared queue; DONE/ is archive.
- Avoid touching KEYS/.env; keep changes logged in GROTA_LOG.md.
