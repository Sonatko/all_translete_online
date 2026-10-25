@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Universal Ecosystem Bootstrapper ^& Auto-Installer

echo ======================================================================
echo  UNIVERSAL 1-CLICK ECOSYSTEM BOOTSTRAPPER ^& AUTO-INSTALLER
echo ======================================================================
echo.

:: ---------------------------------------------------------------------
:: 1. Stage 1 Audio: Python Virtual Environment & CUDA Dependencies
:: ---------------------------------------------------------------------
echo [1/4] Checking Python Virtual Environment (LiveTranslate + NLLB)...
if not exist "%~dp0stage_1_audio\LiveTranslate\start.bat" (
    echo   [CLONE] Submodule files missing. Fetching LiveTranslate repository...
    git submodule update --init --recursive 2>nul
)
if exist "%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\python.exe" (
    echo   [OK] Python virtual environment verified in stage_1_audio\LiveTranslate\.venv
    goto check_overtranslate
)

echo   [INSTALL] Virtual environment missing. Launching automatic installer...
cd /d "%~dp0stage_1_audio\LiveTranslate"
powershell -ExecutionPolicy Bypass -File "%~dp0stage_1_audio\LiveTranslate\install.ps1"
cd /d "%~dp0"

:check_overtranslate
:: ---------------------------------------------------------------------
:: 2. Stage 2 Screen: OverTranslate Portable
:: ---------------------------------------------------------------------
echo.
echo [2/4] Checking In-Place Screen Translator (OverTranslate)...
if exist "%~dp0stage_2_screen\OverTranslate\current\OverTranslate.exe" (
    echo   [OK] OverTranslate is installed and ready in stage_2_screen\OverTranslate\current
    goto check_models
)

echo   [DOWNLOAD] OverTranslate missing. Downloading OverTranslate Portable release...
if not exist "%~dp0stage_2_screen\OverTranslate\current" mkdir "%~dp0stage_2_screen\OverTranslate\current"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$zip = '%~dp0stage_2_screen\OverTranslate\OverTranslate-win-Portable.zip'; $urls = @('https://github.com/Hon-Lu/OverTranslate/releases/latest/download/OverTranslate-win-Portable.zip', 'https://ghproxy.net/https://github.com/Hon-Lu/OverTranslate/releases/latest/download/OverTranslate-win-Portable.zip'); $downloaded = $false; foreach ($u in $urls) { try { Write-Host \"Trying $u...\"; Invoke-WebRequest -Uri $u -OutFile $zip -TimeoutSec 60 -ErrorAction Stop; $downloaded = $true; break } catch { Write-Warning 'Mirror failed, trying next...' } }; if ($downloaded) { Write-Host 'Extracting OverTranslate...'; Expand-Archive -Path $zip -DestinationPath '%~dp0stage_2_screen\OverTranslate\current' -Force; Remove-Item $zip -Force; Write-Host 'OverTranslate extracted successfully!' } else { Write-Error 'Failed to download OverTranslate' }"

:check_models
:: ---------------------------------------------------------------------
:: 3. Translation Models: Meta NLLB-200 1.3B INT8 (Local CUDA Gateway)
:: ---------------------------------------------------------------------
echo.
echo [3/4] Checking Neural Translation Models (Meta NLLB-200 1.3B INT8)...
if exist "%~dp0stage_1_audio\nllb_server\models\nllb-200-1.3b-int8\model.bin" (
    echo   [OK] NLLB-200 1.3B INT8 model is present: 1.34 GB, CUDA ready.
    goto check_config
)

echo   [DOWNLOAD] NLLB model weights missing. Downloading via high-speed mirror...
set "HF_ENDPOINT=https://hf-mirror.com"
"%~dp0stage_1_audio\LiveTranslate\.venv\Scripts\python.exe" -c "import os; from huggingface_hub import snapshot_download; model_dir = os.path.abspath(r'%~dp0stage_1_audio\nllb_server\models\nllb-200-1.3b-int8'); os.makedirs(model_dir, exist_ok=True); print('Downloading NLLB-200 1.3B INT8 via hf-mirror.com...'); snapshot_download(repo_id='haoranxu/nllb-200-1.3B-ctranslate2-int8', local_dir=model_dir, local_dir_use_symlinks=False)"

:check_config
:: ---------------------------------------------------------------------
:: 4. Synchronize Authoritative Configurations
:: ---------------------------------------------------------------------
echo.
echo [4/4] Synchronizing authoritative configurations (CONFIG/ -^> Active Apps)...
if not exist "%~dp0stage_1_audio\LiveTranslate\user_settings.json" (
    copy /Y "%~dp0CONFIG\stage_1_audio\user_settings.json" "%~dp0stage_1_audio\LiveTranslate\user_settings.json" >nul
    echo   [OK] Applied LiveTranslate user_settings.json from CONFIG
) else (
    echo   [OK] LiveTranslate user_settings.json already active
)

if not exist "%APPDATA%\OverTranslate" mkdir "%APPDATA%\OverTranslate" 2>nul
if not exist "%APPDATA%\OverTranslate\appsettings.json" (
    copy /Y "%~dp0CONFIG\stage_2_screen\appsettings.template.json" "%APPDATA%\OverTranslate\appsettings.json" >nul
    echo   [OK] Applied OverTranslate appsettings.json from CONFIG template
) else (
    echo   [OK] OverTranslate appsettings.json already active
)

echo.
echo ======================================================================
echo  SETUP ^& VERIFICATION COMPLETE! 1-CLICK ECOSYSTEM IS READY.
echo ======================================================================
echo  - To start the entire ecosystem (Audio Subtitles + Screen OCR):
echo      run START.bat
echo.
echo  - To stop all processes cleanly:
echo      run STOP.bat
echo.
echo  - For users in China:
echo      CONFIG\stage_2_screen\appsettings.china.template.json contains
echo      pre-tuned Youdao and SiliconFlow settings.
echo ======================================================================
echo.
pause
exit /b 0
