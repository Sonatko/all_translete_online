@echo off
chcp 65001 >nul
cd /d "%~dp0"
title OverTranslate (In-Place Screen Translation & Study)

echo ======================================================================
echo  OVERTRANSLATE: IN-PLACE SCREEN & TEXT TRANSLATOR (STAGE 2)
echo ======================================================================
echo.
echo  [Ctrl + Alt + A]  --^> Screenshot Translation (replaces text right on screen)
echo  [Ctrl + Alt + S]  --^> Real-time Continuous Translation (for games/video)
echo  [Ctrl + C + C]    --^> Quick Lookup & Educational Breakdown (OpenRouter)
echo  [Ctrl + Alt + E]  --^> In-place text replacement in text fields
echo  [Ctrl + Alt + W]  --^> Open main OverTranslate window
echo.
echo ======================================================================
echo  Launching OverTranslate in background...
echo ======================================================================

start "" "%~dp0bin\OverTranslate\current\OverTranslate.exe"
exit /b 0
