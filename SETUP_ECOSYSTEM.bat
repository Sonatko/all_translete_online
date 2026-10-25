@echo off
setlocal
cd /d "%~dp0"
title Real-Time Translation & Language Ecosystem Setup

echo ======================================================================
echo  UNIVERSAL SETUP & ENVIRONMENT VERIFIER
echo ======================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\setup.ps1"
echo.
pause
exit /b 0
