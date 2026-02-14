@echo off
set PYTHONPATH=E:\SHAD\GROTA_LUMENA\CORE
E:\LUMENA_VENV\Scripts\python.exe -m uvicorn corex.api_server:app --port 8002
