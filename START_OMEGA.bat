@echo off
setlocal
echo ?? LUMEN OMEGA - INITIALIZING FROM GROTTO...
cd /d E:\SHAD\GROTA_LUMENA
powershell -NoProfile -ExecutionPolicy Bypass -File "%CD%\\APP\\bootloader.ps1"

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ? ERROR: Python is not in PATH.
    pause
    exit /b
)

echo ?? Location: %CD%
echo ?? Starting Pulse (Sync)...
start /b python pulse.py
echo ??? Starting Synapse Updater...
start /b python synapse_updater.py

echo ??? Dashboard Location: %CD%\DASHBOARD
echo ??? Configuration: %CD%\CONFIG
echo.
echo ? ALL SYSTEMS GO. 
echo To run the dashboard locally:
echo cd DASHBOARD
echo npm install && npm run dev
echo.
echo AUUUUUUUUUUUUUUUUU!
pause
