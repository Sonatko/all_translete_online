@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0.."
title Translation Ecosystem - Update Wizard

echo ======================================================================
echo  TRANSLATION ECOSYSTEM - ONE-CLICK AUTO UPDATE
echo ======================================================================
echo.

:: 1. Git Pull Update (if Git is installed)
where git >nul 2>&1
if %errorlevel% equ 0 (
    echo [1/3] Pulling latest updates from Git repository...
    git pull
    if errorlevel 1 (
        echo [WARNING] Git pull reported warnings or conflicts.
        echo Attempting to proceed with local dependency check and ecosystem self-healing...
    ) else (
        echo [*] Git repository updated successfully.
    )
) else (
    echo [1/3] Git CLI not detected. Skipping git pull step.
)
echo.

:: 2. Verify / Update Python Virtual Environment & Requirements
set "ROOT_DIR=%cd%\"
set "VENV_DIR=%ROOT_DIR%stage_3_voice\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [2/3] Virtual environment missing. Running initial setup wizard...
    call "%ROOT_DIR%scripts\setup.bat"
    if errorlevel 1 (
        echo [ERROR] Setup failed.
        pause
        exit /b 1
    )
    goto finish_update
)

echo [2/3] Verifying and updating Python dependencies...
"%VENV_PY%" -m pip install -r "%ROOT_DIR%stage_3_voice\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://pypi.org/simple
if errorlevel 1 (
    echo [WARNING] Pip dependency update had warnings. Continuing with ecosystem bootstrap...
)

:: 3. Run Universal Ecosystem Bootstrapper & Re-apply Patches
echo.
echo [3/3] Synchronizing engineering patches and locale adaptations...
"%VENV_PY%" "%ROOT_DIR%scripts\bootstrap_ecosystem.py"
if errorlevel 1 (
    echo [ERROR] Ecosystem bootstrap failed.
    pause
    exit /b 1
)

:finish_update
echo.
echo ======================================================================
echo  [SUCCESS] UPDATE COMPLETE! SYSTEM IS READY TO RUN.
echo  You can now start the application via START.bat
echo ======================================================================
echo.
pause
exit /b 0

