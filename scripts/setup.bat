@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0.."
title Translation Ecosystem - Setup Wizard

echo ======================================================================
echo  TRANSLATION ECOSYSTEM - AUTOMATIC SETUP FOR NEW PC
echo ======================================================================
echo.

:: 1. Check Python
set "SYS_PY="
where python >nul 2>&1
if %errorlevel% equ 0 (
    set "SYS_PY=python"
) else (
    where py >nul 2>&1
    if %errorlevel% equ 0 set "SYS_PY=py -3"
)

if not defined SYS_PY (
    echo [*] Python not found in PATH.
    echo [*] Installing Python 3.12 via winget...
    winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to install Python automatically.
        echo Please install Python 3.11 or 3.12 from python.org with 'Add Python to PATH' checked.
        pause
        exit /b 1
    )
    set "SYS_PY=python"
)

echo [1/3] Python detected: !SYS_PY!

:: 2. Create or Repair Virtual Environment
set "ROOT_DIR=%~dp0.."
set "VENV_DIR=%ROOT_DIR%\stage_3_voice\.venv"
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"

if not exist "%VENV_PY%" (
    echo [2/3] Creating isolated virtual environment in stage_3_voice\.venv...
    !SYS_PY! -m venv "%VENV_DIR%"
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [2/3] Virtual environment exists, verifying dependencies...
)

:: 3. Install Requirements
echo [3/3] Installing core libraries (PySide6, Sherpa-ONNX, CTranslate2, Pocket-TTS)...
"%VENV_PY%" -m pip --version >nul 2>&1
if !errorlevel! neq 0 (
    echo [*] Bootstrapping pip into virtual environment...
    "%VENV_PY%" -m ensurepip --upgrade >nul 2>&1
)
"%VENV_PY%" -m pip install --upgrade pip >nul 2>&1
"%VENV_PY%" -m pip install -r "%ROOT_DIR%\stage_3_voice\requirements.txt"

echo.
echo ======================================================================
echo  [SUCCESS] ECOSYSTEM CONFIGURED AND READY TO RUN ON THIS PC!
echo ======================================================================
echo.
exit /b 0

