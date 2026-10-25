@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Ecosystem Validator

echo ======================================================================
echo  UNIVERSAL 1-CLICK ECOSYSTEM SETUP ^& ENVIRONMENT VALIDATOR
echo ======================================================================
echo.

echo [Stage 1/4] Checking Real-Time Audio Pipeline (LiveTranslate + NLLB)...
if exist "stage_1_audio\LiveTranslate\start.bat" (
    echo   [OK] LiveTranslate installed in stage_1_audio\LiveTranslate
) else (
    echo   [!] LiveTranslate missing in stage_1_audio\LiveTranslate
)
if exist "stage_1_audio\nllb_server\run_server.bat" (
    echo   [OK] NLLB-200 offline translation server present in stage_1_audio\nllb_server
) else (
    echo   [!] NLLB-200 server missing in stage_1_audio\nllb_server
)

echo.
echo [Stage 2/4] Checking Screen In-Place Translator (OverTranslate)...
if exist "stage_2_screen\OverTranslate\current\OverTranslate.exe" (
    echo   [OK] OverTranslate installed in stage_2_screen\OverTranslate
) else (
    echo   [!] OverTranslate.exe missing in stage_2_screen\OverTranslate
)

echo.
echo [Stage 3/4] Checking Spaced Repetition Memory Bridge (Anki)...
where anki.exe >nul 2>&1
if %errorlevel% equ 0 (
    echo   [OK] Anki Desktop is already installed on this machine!
) else (
    if exist "stage_3_anki\installer\anki-26.09.3-win-x64.msi" (
        echo   [OK] Anki installer ready in stage_3_anki\installer\
        echo   -^> Launching Anki installer on your desktop...
        start msiexec /i "%~dp0stage_3_anki\installer\anki-26.09.3-win-x64.msi"
        echo   [OK] Installer window opened on screen!
    ) else (
        echo   [!] Anki installer not found in stage_3_anki\installer\
    )
)

echo.
echo [Stage 4/4] Real-Time Voice Cloning ^& Speech-to-Speech (Planned)...
echo   -^> Stage 4 components will be deployed in stage_4_voice\

echo.
echo ======================================================================
echo  Setup ^& Verification Complete! Quick Run Guide:
echo   * START_EN_RU.bat         : Real-time Audio Translation (English -^> Russian)
echo   * START_ZH_RU.bat         : Real-time Audio Translation (Chinese -^> Russian)
echo   * START_OVERTRANSLATE.bat : Screen In-Place Translation ^& AI Learning
echo   * STOP_ALL.bat            : Stop all running translation processes cleanly
echo ======================================================================
echo.
pause
exit /b 0
