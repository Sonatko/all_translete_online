@echo off
rem Same as Dizcord.bat but keeps a console window open with all log messages (for bug reports).
cd /d "%~dp0"
if not exist "%~dp0runtime\.setup-ok" call "%~dp0setup.bat"
"%~dp0runtime\python.exe" "%~dp0main.py"
pause
