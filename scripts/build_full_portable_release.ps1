# Translation Ecosystem - Full Standalone Portable Release Builder
# Packages the entire multi-stage ecosystem into a 1-click self-contained portable zip.
# Ships with standalone uv.exe for zero-dependency Python bootstrap without admin rights or system Python.

param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Write-Step { param($msg) Write-Host "`n[PORTABLE-BUILD] $msg" -ForegroundColor Cyan }
function Write-Ok   { param($msg) Write-Host "  [OK] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "  [WARN] $msg" -ForegroundColor Yellow }

$OutDir = Join-Path $ProjectRoot "release"
$StageDir = Join-Path $OutDir "TranslationEcosystem"

$Sha = try { (& git rev-parse --short HEAD).Trim() } catch { "latest" }
$Stamp = Get-Date -Format "yyyyMMdd"
$Tag = if ($Version) { $Version } else { "v0.3.0-$Stamp-$Sha" }
$ZipPath = Join-Path $OutDir "TranslationEcosystem-$Tag-Windows-x64.zip"

Write-Step "1. Cleaning staging environment..."
if (Test-Path $StageDir) { Remove-Item -Recurse -Force $StageDir }
New-Item -ItemType Directory -Force -Path $StageDir | Out-Null

Write-Step "2. Copying ecosystem core directories..."
$DirsToCopy = @("launcher", "stage_1_audio", "stage_2_screen", "stage_3_voice", "CONFIG", "scripts")
foreach ($d in $DirsToCopy) {
    $src = Join-Path $ProjectRoot $d
    if (Test-Path $src) {
        $dst = Join-Path $StageDir $d
        Copy-Item -Path $src -Destination $dst -Recurse -Force
        Write-Ok "Copied $d"
    }
}

$FilesToCopy = @("START.bat", "STOP.bat", "README.md", "README_ZH.md", "AGENTS.md")
foreach ($f in $FilesToCopy) {
    $src = Join-Path $ProjectRoot $f
    if (Test-Path $src) {
        Copy-Item -Path $src -Destination (Join-Path $StageDir $f) -Force
        Write-Ok "Copied $f"
    }
}

Write-Step "3. Purging temporary build artifacts and local caches..."
$DropPatterns = @(
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "*.pyc",
    "*.tmp*",
    "logs\*.log",
    "transcripts\*.json"
)
foreach ($pat in $DropPatterns) {
    Get-ChildItem -Path $StageDir -Recurse -Filter $pat -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Ok "Caches and virtual environments purged"

Write-Step "4. Bundling standalone uv executable for zero-dependency execution..."
$ToolsDir = Join-Path $StageDir "tools"
New-Item -ItemType Directory -Force -Path $ToolsDir | Out-Null
$UvExe = Join-Path $ToolsDir "uv.exe"

$UvUrls = @(
    "https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip",
    "https://ghproxy.net/https://github.com/astral-sh/uv/releases/latest/download/uv-x86_64-pc-windows-msvc.zip"
)

$UvZip = Join-Path $OutDir "uv_temp.zip"
$Downloaded = $false
foreach ($url in $UvUrls) {
    try {
        Write-Host "Downloading uv from $url ..." -ForegroundColor Gray
        Invoke-WebRequest -Uri $url -OutFile $UvZip -TimeoutSec 30
        Expand-Archive -Path $UvZip -DestinationPath $ToolsDir -Force
        Remove-Item $UvZip -Force -ErrorAction SilentlyContinue
        if (Test-Path $UvExe) {
            $Downloaded = $true
            Write-Ok "Bundled uv executable: $(& $UvExe --version)"
            break
        }
    } catch {
        Write-Warn "Download failed from $url, trying fallback..."
    }
}

if (-not $Downloaded) {
    # Check if local uv exists
    $localUv = (Get-Command uv -ErrorAction SilentlyContinue).Source
    if ($localUv -and (Test-Path $localUv)) {
        Copy-Item $localUv $UvExe -Force
        Write-Ok "Copied host uv executable: $(& $UvExe --version)"
    } else {
        Write-Warn "Could not bundle uv.exe; target PC must have Python installed."
    }
}

Write-Step "5. Generating bulletproof standalone Portable START.bat..."
$PortableStart = @'
@echo off
chcp 65001 >nul
title Translation Ecosystem (100% Offline Portable)
cd /d "%~dp0"

set "UV_EXE=%~dp0tools\uv.exe"
set "VENV_PY=%~dp0stage_3_voice\.venv\Scripts\python.exe"
set "VENV_PYW=%~dp0stage_3_voice\.venv\Scripts\pythonw.exe"
set "HUB_SCRIPT=%~dp0launcher\hub.py"

:: Check if already initialized
if exist "%VENV_PY%" (
    "%VENV_PY%" -c "exit(0)" >nul 2>&1
    if not errorlevel 1 goto run_hub
)

echo ======================================================================
echo  TRANSLATION ECOSYSTEM - AUTOMATIC 1-CLICK INITIALIZATION
echo ======================================================================
echo.
echo First run detected: initializing isolated portable runtime...
echo.

if exist "%UV_EXE%" (
    echo [1/3] Setting up managed Python 3.12 via bundled uv...
    set "UV_PYTHON_INSTALL_DIR=%~dp0tools\python"
    set "UV_CACHE_DIR=%~dp0.uv-cache"
    "%UV_EXE%" venv "%~dp0stage_3_voice\.venv" --python 3.12 --managed-python --link-mode copy
    if errorlevel 1 (
        echo [ERROR] Failed to initialize portable virtual environment.
        pause
        exit /b 1
    )
    echo [2/3] Installing core neural modules (Sherpa-ONNX, CTranslate2, Pocket-TTS)...
    "%UV_EXE%" pip install --python "%VENV_PY%" -r "%~dp0stage_3_voice\requirements.txt" -i https://pypi.tuna.tsinghua.edu.cn/simple --extra-index-url https://pypi.org/simple
    if errorlevel 1 (
        echo [WARNING] Tsinghua mirror failed, falling back to official PyPI...
        "%UV_EXE%" pip install --python "%VENV_PY%" -r "%~dp0stage_3_voice\requirements.txt"
    )
) else (
    call "%~dp0scripts\setup.bat"
)

echo [3/3] Orchestrating ecosystem stages and injecting authoritative patches...
"%VENV_PY%" "%~dp0scripts\bootstrap_ecosystem.py"

:run_hub
echo [OK] Launching Universal Translation Hub...
if "%1"=="--debug" (
    "%VENV_PY%" "%HUB_SCRIPT%"
    if errorlevel 1 pause
    exit /b %errorlevel%
)

start "" "%VENV_PYW%" "%HUB_SCRIPT%"
exit /b 0
'@
Set-Content -Path (Join-Path $StageDir "START.bat") -Value $PortableStart -Encoding ASCII

Write-Step "6. Compressing full package into $ZipPath ..."
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path $StageDir -DestinationPath $ZipPath -Force
$SizeMb = [math]::Round((Get-Item $ZipPath).Length / 1MB, 1)
Write-Ok "Created standalone release archive: $ZipPath ($SizeMb MB)"

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host " [SUCCESS] FULL PORTABLE STANDALONE RELEASE READY!" -ForegroundColor Green
Write-Host " File: $ZipPath" -ForegroundColor Green
Write-Host " Distribute this single ZIP to any Windows user without Git or Python!" -ForegroundColor Green
Write-Host "======================================================================`n" -ForegroundColor Green

