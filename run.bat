@echo off
REM One-click launcher for Nova Goods. Kills any running instance on :8000, then restarts.
cd /d "%~dp0"

REM restart-on-run: kill whatever is already listening on port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /f /pid %%a >nul 2>&1

REM open the browser once the server has had time to load the model (detached waiter)
REM ponytail: fixed 8s guess; model load can be slower on a cold start -> just refresh the tab if blank
start "" cmd /c "timeout /t 8 >nul & start "" http://127.0.0.1:8000/"

echo Starting Nova Goods on http://127.0.0.1:8000  (close this window to stop)
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
