@echo off
setlocal
cd /d "%~dp0"
title Renaming Topping Audio Endpoints...

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell.exe -NoProfile -Command "Start-Process powershell.exe -Verb RunAs -ArgumentList '-NoProfile -ExecutionPolicy Bypass -File """"%~dp0rename_audio.ps1""""'"
    exit /b 0
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0rename_audio.ps1"
exit /b 0
