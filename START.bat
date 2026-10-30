@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe"
set "VENV_PYW=%~dp0stage_3_voice\Dizcord\.venv\Scripts\pythonw.exe"
set "HUB_SCRIPT=%~dp0launcher\hub.py"

if not exist "%VENV_PY%" goto need_setup
"%VENV_PY%" -c "exit(0)" >nul 2>&1
if not errorlevel 1 goto launch_hub

:need_setup
echo ======================================================================
echo  FIRST-TIME SETUP / NEW PC DETECTED: AUTO-PREPARING ENVIRONMENT
echo ======================================================================
echo.
echo Virtual environment missing or copied from another machine.
echo Running automatic bootstrap setup (takes ~1 minute)...
echo.
call "%~dp0scripts\setup.bat"
if errorlevel 1 (
    echo.
    echo [ERROR] Setup failed. Please check your internet connection.
    pause
    exit /b 1
)

:launch_hub
if "%1"=="--debug" (
    echo [INFO] Starting Translation Ecosystem Hub in console debug mode...
    "%VENV_PY%" "%HUB_SCRIPT%"
    if errorlevel 1 pause
    exit /b %errorlevel%
)

start "" "%VENV_PYW%" "%HUB_SCRIPT%"
exit /b 0
