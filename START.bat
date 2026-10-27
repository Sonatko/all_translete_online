@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Hub [Online/Active]

echo ======================================================================
echo  UNIVERSAL REAL-TIME TRANSLATION ECOSYSTEM (IN-PROCESS NLLB)
echo ======================================================================
echo.

:: ---------------------------------------------------------------------
:: 1. LiveTranslate Subtitle Overlay (Stage 1.1 ASR ONNX)
:: ---------------------------------------------------------------------
echo [1/2] Launching LiveTranslate Subtitle Overlay (Stage 1.1 ASR + Stage 1.2 MT)...
set "LIVETRANSLATE_SETTINGS_FILE=%~dp0stage_1_audio\LiveTranslate\user_settings.json"
cd /d "%~dp0stage_1_audio\LiveTranslate"
start "" "%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\pythonw.exe" main.py
if errorlevel 1 (
    echo [ERROR] Failed to start LiveTranslate.
    pause
    exit /b 1
)
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: 2. OverTranslate In-Place Screen Translator (Stage 2)
:: ---------------------------------------------------------------------
echo [2/2] Launching OverTranslate In-Place Screen Translator (Stage 2)...
cd /d "%~dp0stage_2_screen\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: Dashboard & Hotkeys
:: ---------------------------------------------------------------------
echo.
echo ======================================================================
echo  TRANSLATION ECOSYSTEM IS ONLINE AND READY!
echo ======================================================================
echo  [Stage 1: Real-Time Audio Translation - LiveTranslate]
echo  - Engine: Sherpa-ONNX INT8 (SenseVoice) + Tencent HY-MT 1.8B GGUF
echo  - Status: Dual-Language Subtitles (Original EN + Translated RU)
echo  - F9:           Master Toggle (Subtitles Show/Hide + Audio Run/Pause)
echo  - 2x MMB:       Double Middle Click to toggle Click-through (Lock/Unlock)
echo  - MMB Drag:     Drag subtitle banner with Middle Mouse Button (wheel)
echo.
echo  [Stage 2: Screen OCR ^& Text - OverTranslate]
echo  - Ctrl+Alt+A:   Screen OCR In-Place Translation (Drag bounding box)
echo  - Ctrl+C+C:     Instant QuickLookup ^& Context Breakdown (Double Copy)
echo  - Ctrl+Alt+W:   Show / Hide OverTranslate Main Window
echo ======================================================================
echo  To stop all services cleanly, run STOP.bat
echo ======================================================================
echo.
echo Closing launcher window in 4 seconds...
ping 127.0.0.1 -n 5 >nul
exit /b 0
