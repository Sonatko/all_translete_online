@echo off
setlocal
cd /d "%~dp0"
title Translation Ecosystem - Automated Test Suite

set "VENV_PY=%~dp0stage_3_voice\Dizcord\.venv\Scripts\python.exe"

if not exist "%VENV_PY%" goto err_no_venv

echo ======================================================================
echo  RUNNING COMPREHENSIVE VERIFICATION TEST SUITE
echo ======================================================================
echo.

"%VENV_PY%" "%~dp0tests\test_stage3_and_hub_verification.py"
set "TEST_RES=%errorlevel%"

echo.
if %TEST_RES% equ 0 goto test_ok
goto test_fail

:test_ok
echo ======================================================================
echo  [SUCCESS] ALL VERIFICATION GATES PASSED (EXIT CODE 0)
echo ======================================================================
goto end

:test_fail
echo ======================================================================
echo  [FAILURE] ONE OR MORE TESTS FAILED (EXIT CODE %TEST_RES%)
echo ======================================================================
goto end

:err_no_venv
echo [ERROR] Virtual environment not found at:
echo %VENV_PY%
echo Please run START.bat or SETUP.bat first to initialize the environment.
set "TEST_RES=1"

:end
echo.
if not "%1"=="--no-pause" pause
exit /b %TEST_RES%
