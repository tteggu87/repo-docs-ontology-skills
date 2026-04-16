@echo off
setlocal

set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

echo [1/4] Checking required commands...
where py >nul 2>nul
if %ERRORLEVEL%==0 (
  set "PYTHON_CMD=py -3"
) else (
  where python >nul 2>nul
  if %ERRORLEVEL%==0 (
    set "PYTHON_CMD=python"
  ) else (
    echo ERROR: Python was not found. Install Python 3 first.
    exit /b 1
  )
)

where npm >nul 2>nul
if not %ERRORLEVEL%==0 (
  echo ERROR: npm was not found. Install Node.js first.
  exit /b 1
)

echo [2/4] Creating virtual environment...
%PYTHON_CMD% -m venv .venv
if not %ERRORLEVEL%==0 (
  echo ERROR: Failed to create the virtual environment.
  exit /b 1
)

echo [3/4] Installing Python dependency...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
if not %ERRORLEVEL%==0 (
  echo ERROR: Failed to upgrade pip.
  exit /b 1
)

pip install pyyaml
if not %ERRORLEVEL%==0 (
  echo ERROR: Failed to install PyYAML.
  exit /b 1
)

echo [4/4] Installing frontend dependencies...
cd /d "%ROOT_DIR%apps\workbench"
npm ci
if not %ERRORLEVEL%==0 (
  echo ERROR: Failed to install frontend dependencies.
  exit /b 1
)

cd /d "%ROOT_DIR%"
echo.
echo Windows setup completed successfully.
echo Run run_windows_workbench.bat to start the API server and the workbench UI.
exit /b 0
