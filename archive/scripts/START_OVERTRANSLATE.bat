@echo off
setlocal
cd /d "%~dp0"
title OverTranslate Launcher

echo ======================================================================
echo  OVERTRANSLATE: IN-PLACE SCREEN AND TEXT TRANSLATOR (STAGE 2)
echo ======================================================================
echo.

echo [1/3] Closing any previous or background instances...
taskkill /F /IM OverTranslate.exe >nul 2>&1

echo [2/3] Launching OverTranslate on your desktop...
cd /d "%~dp0stage_2_screen\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"

echo [3/3] Opening OverTranslate main window...
ping 127.0.0.1 -n 3 >nul
cd /d "%~dp0stage_2_screen\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"

echo.
echo ======================================================================
echo  OVERTRANSLATE IS ACTIVE!
echo  - Window:  Opened in center of screen
echo  - Hotkey:  [Ctrl + Alt + A] - Screen OCR Translation
echo  - Lookup:  [Ctrl + C + C]   - AI Word / Context Breakdown
echo  - Toggle:  [Ctrl + Alt + W] - Show / Hide Main Window
echo ======================================================================
echo.
echo Closing launcher in 3 seconds...
ping 127.0.0.1 -n 4 >nul
exit /b 0
