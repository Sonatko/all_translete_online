@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Real-Time Translation Ecosystem Orchestrator

:MENU
cls
echo ======================================================================
echo    ГЛАВНЫЙ ОРКЕСТРАТОР ЭКОСИСТЕМЫ ПЕРЕВОДА В РЕАЛЬНОМ ВРЕМЕНИ
echo ======================================================================
echo.
echo  [1] ОТКРЫТЬ ГРАФИЧЕСКИЙ ЦЕНТР УПРАВЛЕНИЯ (GUI HUB)
echo  [2] Запустить ВСЮ экосистему разом (Этапы 1, 2, 3)
echo  [3] Запустить только Этап 1: Входящие субтитры (LiveTranslate)
echo  [4] Запустить только Этап 2: Экранный переводчик (OverTranslate)
echo  [5] Запустить только Этап 3: Студия голоса CS2 (Voice Studio)
echo.
echo  ----------------------------------------------------------------------
echo  [6] Запустить мастер клонирования голоса под себя (RECORD_MY_VOICE)
echo  [9] ОСТАНОВИТЬ ВСЕ ЗАПУЩЕННЫЕ МОДУЛИ (STOP.bat)
echo  [0] Выход
echo ======================================================================
echo.
set /p CHOICE="Выберите действие [0-9] и нажмите Enter: "

if "%CHOICE%"=="1" goto LAUNCH_HUB
if "%CHOICE%"=="2" goto START_ALL
if "%CHOICE%"=="3" goto START_STAGE1
if "%CHOICE%"=="4" goto START_STAGE2
if "%CHOICE%"=="5" goto START_STAGE3
if "%CHOICE%"=="6" goto RECORD_VOICE
if "%CHOICE%"=="9" goto STOP_ALL
if "%CHOICE%"=="0" exit /b 0

echo Неверный ввод, повторите попытку...
timeout /t 2 >nul
goto MENU

:LAUNCH_HUB
echo.
echo [▶] Запуск графического Центра Управления...
call "%~dp0LAUNCHER.bat"
goto MENU

:START_ALL
echo.
echo [▶] Запуск полной экосистемы (Этапы 1, 2 и 3)...
call "%~dp0START.bat"
goto MENU

:START_STAGE1
echo.
echo [▶] Запуск Этапа 1 (LiveTranslate)...
set "LIVETRANSLATE_SETTINGS_FILE=%~dp0stage_1_audio\LiveTranslate\user_settings.json"
cd /d "%~dp0stage_1_audio\LiveTranslate"
start "" "%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\pythonw.exe" main.py
cd /d "%~dp0"
timeout /t 2 >nul
goto MENU

:START_STAGE2
echo.
echo [▶] Запуск Этапа 2 (OverTranslate)...
cd /d "%~dp0stage_2_screen\OverTranslate\current"
start "" OverTranslate.exe
cd /d "%~dp0"
timeout /t 2 >nul
goto MENU

:START_STAGE3
echo.
echo [▶] Запуск Этапа 3 (Voice Translation Studio)...
start "" "%~dp0START_STAGE3_STUDIO.bat"
timeout /t 2 >nul
goto MENU

:RECORD_VOICE
echo.
echo [▶] Запуск записи и клонирования голоса...
call "%~dp0RECORD_MY_VOICE.bat"
goto MENU

:STOP_ALL
echo.
echo [⏹] Остановка всех модулей...
call "%~dp0STOP.bat"
goto MENU
