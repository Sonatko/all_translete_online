@echo off
setlocal
cd /d "%~dp0"

set "VENV_PY=%~dp0stage_3_voice\.venv\Scripts\python.exe"
set "VENV_PYW=%~dp0stage_3_voice\.venv\Scripts\pythonw.exe"
set "HUB_SCRIPT=%~dp0launcher\hub.py"

if not exist "%VENV_PY%" goto need_setup
if not exist "%~dp0stage_2_screen\OverTranslate\current\OverTranslate.exe" goto need_setup
"%VENV_PY%" -c "exit(0)" >nul 2>&1
if not errorlevel 1 goto launch_hub

:need_setup
echo ======================================================================
echo  FIRST-TIME SETUP / NEW PC DETECTED: AUTO-PREPARING ENVIRONMENT
echo ======================================================================
echo.
echo Components missing or environment not initialized.
echo Running automatic bootstrap setup (takes ~1 minute)...
echo.
call "%~dp0scripts\setup.bat"
if errorlevel 1 (
    echo.
    echo [ERROR] Setup failed. Please check your internet connection.
    pause
    exit /b 1
)







on Ecosystem Hub in console debug mode...











%"



