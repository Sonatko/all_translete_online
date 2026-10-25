<#
.SYNOPSIS
    Universal 1-Click Installer and Setup Script for Real-Time Translation & Language Hub.
.DESCRIPTION
    Installs, validates, and prepares all ecosystem components for Windows:
    - Stage 1: Audio Translation (LiveTranslate + NLLB-200 Server)
    - Stage 2: Screen In-Place Translation (OverTranslate)
    - Stage 3: Spaced Repetition Memory Bridge (Anki Desktop)
    - Stage 4: Real-Time Speech-to-Speech & Voice Cloning (Planned)
#>

[CmdletBinding()]
param (
    [switch]$SkipAnki = $false
)

$ErrorActionPreference = "Continue"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Universal Real-Time Translation & Language Ecosystem Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$BinDir = Join-Path $WorkspaceRoot "bin"
$DownloadsDir = Join-Path $WorkspaceRoot "downloads"
$ConfigsDir = Join-Path $WorkspaceRoot "configs"

# ---------------------------------------------------------------------
# 1. Check Python & Audio Pipeline (Stage 1)
# ---------------------------------------------------------------------
Write-Host "`n[Stage 1/4] Checking Real-Time Audio Pipeline (LiveTranslate + NLLB)..." -ForegroundColor Yellow
$LiveTranslateDir = Join-Path $BinDir "LiveTranslate"
$NllbDir = Join-Path $BinDir "nllb_server"

if (Test-Path (Join-Path $LiveTranslateDir "start.bat")) {
    Write-Host "  [OK] LiveTranslate installed at: $LiveTranslateDir" -ForegroundColor Green
} else {
    Write-Warning "  [!] LiveTranslate directory missing in bin/LiveTranslate."
}

if (Test-Path (Join-Path $NllbDir "run_server.bat")) {
    Write-Host "  [OK] NLLB-200 offline translation server present at: $NllbDir" -ForegroundColor Green
} else {
    Write-Warning "  [!] nllb_server missing in bin/nllb_server."
}

# ---------------------------------------------------------------------
# 2. Check OverTranslate (Stage 2)
# ---------------------------------------------------------------------
Write-Host "`n[Stage 2/4] Checking Screen In-Place Translator (OverTranslate)..." -ForegroundColor Yellow
$OverTranslateExe = Join-Path $BinDir "OverTranslate\current\OverTranslate.exe"

if (Test-Path $OverTranslateExe) {
    Write-Host "  [OK] OverTranslate installed at: $OverTranslateExe" -ForegroundColor Green
} else {
    Write-Warning "  [!] OverTranslate.exe not found in bin/OverTranslate/current/."
}

# Deploy configuration template if appsettings.json does not exist yet
$AppDataOT = Join-Path $env:APPDATA "OverTranslate"
$TargetSettings = Join-Path $AppDataOT "appsettings.json"
$TemplateSettings = Join-Path $ConfigsDir "overtranslate\appsettings.template.json"

if (-not (Test-Path $TargetSettings) -and (Test-Path $TemplateSettings)) {
    Write-Host "  -> Initializing OverTranslate default config from template..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $AppDataOT -Force | Out-Null
    Copy-Item -Path $TemplateSettings -Destination $TargetSettings -Force
    Write-Host "  [OK] OverTranslate configuration deployed to %APPDATA%\OverTranslate" -ForegroundColor Green
}

# ---------------------------------------------------------------------
# 3. Check & Install Anki Desktop (Stage 3)
# ---------------------------------------------------------------------
Write-Host "`n[Stage 3/4] Checking Spaced Repetition Memory Bridge (Anki)..." -ForegroundColor Yellow
$AnkiCmd = Get-Command "anki" -ErrorAction SilentlyContinue

if ($AnkiCmd) {
    Write-Host "  [OK] Anki is already installed on this machine: $($AnkiCmd.Source)" -ForegroundColor Green
} else {
    $AnkiMsi = Join-Path $DownloadsDir "anki-26.09.3-win-x64.msi"
    if (Test-Path $AnkiMsi) {
        if (-not $SkipAnki) {
            Write-Host "  -> Launching Anki installer from downloads directory..." -ForegroundColor Cyan
            Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$AnkiMsi`"" -Wait
            Write-Host "  [OK] Anki installation process finished!" -ForegroundColor Green
        } else {
            Write-Host "  -> Anki installer is available at: $AnkiMsi (skipped by switch)" -ForegroundColor White
        }
    } else {
        Write-Warning "  [!] Anki installer not found in downloads/. Download from: https://apps.ankiweb.net/"
    }
}

# ---------------------------------------------------------------------
# 4. Stage 4 Preview (Speech-to-Speech)
# ---------------------------------------------------------------------
Write-Host "`n[Stage 4/4] Real-Time Voice Cloning & Speech-to-Speech (Planned)..." -ForegroundColor Yellow
Write-Host "  -> Stage 4 components will be deployed in stage_4_voice/." -ForegroundColor White

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Setup & Verification Complete! Quick Run Guide:" -ForegroundColor Green
Write-Host "  * START_EN_RU.bat         : Real-time Audio Translation (English -> Russian)" -ForegroundColor White
Write-Host "  * START_ZH_RU.bat         : Real-time Audio Translation (Chinese -> Russian)" -ForegroundColor White
Write-Host "  * START_OVERTRANSLATE.bat : Screen In-Place Translation & AI Learning (Groq LPU)" -ForegroundColor White
Write-Host "  * STOP_ALL.bat            : Stop all running translation processes cleanly" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
