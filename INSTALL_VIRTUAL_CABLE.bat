@echo off
setlocal
cd /d "%~dp0"

net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process cmd -ArgumentList '/c `\"%~f0`\"' -Verb RunAs"
    exit /b
)

echo ======================================================================
echo  VB-AUDIO VIRTUAL CABLE - 1-CLICK AUTOMATIC INSTALLER
echo ======================================================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install_vbcable.ps1"
echo.
pause
exit /b 0
