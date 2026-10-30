@echo off
title Dizcord - setup
cd /d "%~dp0"
echo.
echo  Dizcord Translator - portable setup
echo  Everything is installed inside this folder (runtime\). No admin rights needed.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\setup.ps1"
if errorlevel 1 (
  echo.
  echo  Setup FAILED - check your internet connection and run setup.bat again.
  pause
  exit /b 1
)
echo.
pause
