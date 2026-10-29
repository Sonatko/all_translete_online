@echo off
setlocal
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process cmd -ArgumentList '/c `\"%~f0`\"' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo  RENAMING TOPPING AUDIO DEVICES TO SHORT CLEAN NAMES
echo ======================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\rename_audio.ps1"
echo.
echo [OK] Devices renamed successfully!
echo.
pause
exit /b 0
