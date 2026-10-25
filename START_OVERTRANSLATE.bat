@echo off
setlocal
cd /d "%~dp0"
title OverTranslate (Screen and Image Translation Hub)

echo ======================================================================
echo  OVERTRANSLATE: IN-PLACE SCREEN AND TEXT TRANSLATOR (STAGE 2)
echo ======================================================================
echo.

tasklist /FI "IMAGENAME eq OverTranslate.exe" 2>nul | findstr /I "OverTranslate.exe" >nul
if %errorlevel% equ 0 (
    echo [INFO] OverTranslate is already running in background!
    echo [INFO] Bringing OverTranslate main window to front...
    cd /d "%~dp0bin\OverTranslate\current"
    start "" OverTranslate.exe
    cd /d "%~dp0"
    goto show_instructions
)

echo [1/2] Launching OverTranslate...
cd /d "%~dp0bin\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"

ping 127.0.0.1 -n 3 >nul

rem Secondary launch triggers OverTranslate_Activate event to display ShellWindow
cd /d "%~dp0bin\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"

:show_instructions
echo.
echo ======================================================================
echo  OVERTRANSLATE HOTKEYS READY TO USE:
echo ======================================================================
echo.
echo  [Ctrl + Alt + A]  - Screen Translation (replaces text right on screen)
echo  [Ctrl + C + C]    - Word / Sentence Breakdown (OpenRouter AI Learning)
echo  [Ctrl + Alt + S]  - Streaming OCR Translation (Game cutscenes)
echo  [Ctrl + Alt + W]  - Show / Hide OverTranslate main window
echo.
echo ======================================================================
echo  Tray Icon is active in Windows notification area (near the clock).
echo ======================================================================
echo.
echo Press any key to close this launcher console...
pause >nul
exit /b 0
