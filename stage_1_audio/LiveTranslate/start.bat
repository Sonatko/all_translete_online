@echo off
cd /d "%~dp0"
set PATH=%LOCALAPPDATA%\Microsoft\WinGet\Links;%PATH%

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found.
    echo Please run install.bat first to set up the environment.
    echo.
    pause
    exit /b 1
)

if not exist ".venv\.livetranslate-ready" (
    echo [ERROR] Virtual environment setup is incomplete.
    echo Please run install.bat again to finish installing and verifying dependencies.
    echo.
    pause
    exit /b 1
)

echo Starting LiveTranslate...
start "LiveTranslate" "%~dp0.venv\Scripts\python.exe" "%~dp0main.py"
exit /b 0
