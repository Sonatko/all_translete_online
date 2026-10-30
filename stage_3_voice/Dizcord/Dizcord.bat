@echo off
cd /d "%~dp0"
if not exist "%~dp0runtime\.setup-ok" (
  echo First start: setting up the portable runtime...
  call "%~dp0setup.bat"
  if not exist "%~dp0runtime\.setup-ok" exit /b 1
)
start "" "%~dp0runtime\pythonw.exe" "%~dp0main.py"
