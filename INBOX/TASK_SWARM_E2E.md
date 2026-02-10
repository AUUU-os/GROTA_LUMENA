# TASK SWARM: E2E TEAM
## DLA: SWARM
## OD: CODEX
## PRIORYTET: HIGH
## OPIS: Uruchomic swarm agents end-to-end i potwierdzic routing agent_role wg task_type.
## KONTEKST: CORE/corex/swarm/*, smart_router.py, engine.py
## KRYTERIA AKCEPTACJI:
- /api/v1/swarm/health OK
- /api/v1/swarm/routes OK
- smart_dispatch returns agent_role in metadata
