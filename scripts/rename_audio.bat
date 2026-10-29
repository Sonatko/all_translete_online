@echo off
setlocal
cd /d "%~dp0"
title Renaming Topping Audio Endpoints...

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0rename_audio.ps1"
exit /b %errorlevel%
