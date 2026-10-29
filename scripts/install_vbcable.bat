@echo off
setlocal
cd /d "%~dp0"
title Installing VB-Audio Virtual Cable...

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install_vbcable.ps1"
exit /b %errorlevel%
