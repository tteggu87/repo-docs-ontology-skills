@echo off
setlocal

set "REPO_DIR=%~dp0"
if "%REPO_DIR:~-1%"=="\" set "REPO_DIR=%REPO_DIR:~0,-1%"
set "APP_DIR=%REPO_DIR%\apps\doctology-workbench"
set "URL=http://127.0.0.1:4173"

echo ============================================
echo  Run DocTology Workbench GUI
echo ============================================
echo.
echo Repo:   %REPO_DIR%
echo App:    %APP_DIR%
echo URL:    %URL%
echo.

if not exist "%APP_DIR%\package.json" (
  echo ERROR: workbench app not found
  echo %APP_DIR%\package.json
  echo.
  pause
  exit /b 1
)

cd /d "%APP_DIR%"

if not exist "node_modules" (
  echo node_modules not found. Running npm install...
  call npm install
  if errorlevel 1 (
    echo.
    echo npm install failed.
    pause
    exit /b 1
  )
  echo.
)

start "" "%URL%"

echo Starting Vite dev server...
echo Press Ctrl+C to stop.
echo.

call npm run dev -- --host 127.0.0.1 --port 4173

echo.
echo Workbench stopped.
echo.
pause
