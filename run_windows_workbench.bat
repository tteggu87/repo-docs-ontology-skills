@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

if not exist ".venv\Scripts\activate.bat" (
  echo ERROR: Virtual environment not found.
  echo Run install_windows.bat first.
  exit /b 1
)

where npm >nul 2>nul
if not %ERRORLEVEL%==0 (
  echo ERROR: npm was not found. Install Node.js first.
  exit /b 1
)

echo Starting LLM Wiki workbench services...
echo API:      http://127.0.0.1:8765
echo Frontend: http://127.0.0.1:4174/#home
echo.

start "LLM Wiki API" cmd /k "cd /d \"%ROOT_DIR%\" && call .venv\Scripts\activate.bat && python scripts\workbench_api.py --serve"
start "LLM Wiki Frontend" cmd /k "cd /d \"%ROOT_DIR%apps\workbench\" && npm run dev -- --host 127.0.0.1 --port 4174"

timeout /t 2 /nobreak >nul
start "" "http://127.0.0.1:4174/#home"

echo Two windows were opened for the API server and the frontend dev server.
echo Close those windows to stop the services.
exit /b 0
