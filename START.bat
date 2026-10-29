@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Ecosystem [Full Online Hub]

echo ======================================================================
echo  UNIVERSAL REAL-TIME TRANSLATION ECOSYSTEM (STAGES 1, 2, 3)
echo ======================================================================
echo.

:: ---------------------------------------------------------------------
:: 1. LiveTranslate Subtitle Overlay (Stage 1 Incoming Audio)
:: ---------------------------------------------------------------------
echo [1/3] Launching LiveTranslate Subtitle Overlay (Stage 1 ASR + MT)...
set "LIVETRANSLATE_SETTINGS_FILE=%~dp0stage_1_audio\LiveTranslate\user_settings.json"
cd /d "%~dp0stage_1_audio\LiveTranslate"
start "" "%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\pythonw.exe" main.py
if errorlevel 1 (
    echo [ERROR] Failed to start LiveTranslate.
)
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: 2. OverTranslate In-Place Screen Translator (Stage 2 Screen OCR)
:: ---------------------------------------------------------------------
echo [2/3] Launching OverTranslate Screen Translator (Stage 2 OCR)...
cd /d "%~dp0stage_2_screen\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: 3. Voice Translation Studio (Stage 3 Outgoing Voice in CS2/Discord)
:: ---------------------------------------------------------------------
echo [3/3] Launching Voice Translation Studio (Stage 3 S2ST)...
cd /d "%~dp0stage_3_voice\studio"
start "" "%~dp0stage_3_voice\Dizcord\.venv\Scripts\pythonw.exe" main.py
cd /d "%~dp0"

:: ---------------------------------------------------------------------
:: Dashboard & Hotkeys
:: ---------------------------------------------------------------------
echo.
echo ======================================================================
echo  TRANSLATION ECOSYSTEM IS ONLINE AND READY!
echo ======================================================================
echo  [Stage 1: Real-Time Audio Translation - LiveTranslate]
echo  - Subtitles:       Dual-Language (Original EN + Translated RU)
echo  - F9:              Master Toggle (Subtitles Show/Hide + Audio Run/Pause)
echo  - 2x MMB:          Double Middle Click to toggle Click-through (Lock/Unlock)
echo  - MMB Drag:        Drag subtitle banner with Middle Mouse Button (wheel)
echo.
echo  [Stage 2: Screen OCR ^& Text - OverTranslate]
echo  - Ctrl+Alt+A:      Screen OCR In-Place Translation (Drag bounding box)
echo  - Ctrl+C+C:        Instant QuickLookup ^& Context Breakdown (Double Copy)
echo  - Ctrl+Alt+C:      QuickTranslate (In-Place Text Replacement)
echo  - Ctrl+Alt+W:      Show / Hide OverTranslate Main Window
echo.
echo  [Stage 3: Outgoing Voice S2ST - Voice Studio (CS2 ^& Discord)]
echo  - Shift + MMB:     Push-to-Talk (Hold to speak English in your cloned voice)
echo  - Passthrough:     Natural Russian mic passes when PTT is released
echo  - Routing:         Outputs to Topping Playback 3/4 -^> Loopback 1+2
echo ======================================================================
echo  To stop all services cleanly, run STOP.bat
echo ======================================================================
echo.
echo Closing launcher window in 5 seconds...
ping 127.0.0.1 -n 6 >nul
exit /b 0
