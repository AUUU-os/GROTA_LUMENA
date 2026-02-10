# CI Checklist (Local)

- `pip install -r CORE/requirements.txt`
- `pytest` in `CORE/` (if tests exist)
- `npm install` in `DASHBOARD/`
- `npm run build` in `DASHBOARD/`
- Run `python CORE/corex/api_server.py` and verify `/api/v1/health`
