@echo off
setlocal
cd /d "%~dp0"
title Renaming Audio Devices...

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell.exe -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b 0
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0rename_audio.ps1"
exit /b 0
