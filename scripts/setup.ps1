<#
.SYNOPSIS
    Universal Setup Script for Real-Time Audio & Text Translation Hub.
.DESCRIPTION
    Configures Pot-Desktop for Screen OCR / selection translation and verifies LiveTranslate environment.
#>

[CmdletBinding()]
param (
    [switch]$SkipInstall = $false
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " Universal Real-Time Translation & Language Learning Setup" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$WorkspaceRoot = Split-Path -Parent $PSScriptRoot
$BinDir = Join-Path $WorkspaceRoot "bin"
$LiveTranslateDir = Join-Path $BinDir "LiveTranslate"

# 1. Check Pot-Desktop (Screen OCR & Selection Translation)
Write-Host "`n[Step 1/2] Checking Pot-Desktop (Screen OCR & Text Translator)..." -ForegroundColor Yellow
$potInstalled = (Get-Command "pot" -ErrorAction SilentlyContinue) -ne $null

if ($potInstalled) {
    Write-Host "  -> Pot-Desktop is already installed on this machine." -ForegroundColor Green
} else {
    if (-not $SkipInstall) {
        Write-Host "  -> Installing Pot-Desktop via Windows Package Manager (winget)..." -ForegroundColor Cyan
        try {
            winget install --id Pylogmon.pot -e --source winget --accept-package-agreements --accept-source-agreements
            Write-Host "  -> Pot-Desktop installed successfully!" -ForegroundColor Green
        } catch {
            Write-Warning "  -> Winget auto-install failed. Manual download link: https://github.com/pot-app/pot-desktop/releases"
        }
    }
}

# 2. Check LiveTranslate (Audio & Subtitles)
Write-Host "`n[Step 2/2] Checking LiveTranslate (Real-time Audio & Cinema Subtitles)..." -ForegroundColor Yellow
if (Test-Path (Join-Path $LiveTranslateDir "start.bat")) {
    Write-Host "  -> LiveTranslate is installed and ready at: $LiveTranslateDir" -ForegroundColor Green
} else {
    Write-Warning "  -> LiveTranslate directory not found in bin/."
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Setup complete! Quick Start Checklist:" -ForegroundColor Green
Write-Host " 1. Start audio translation: Run bin\LiveTranslate\start.bat" -ForegroundColor White
Write-Host "    - F9 toggles Subtitles + Run/Stop master switch." -ForegroundColor White
Write-Host "    - Double-click mouse wheel over subtitles to toggle Click-through on/off." -ForegroundColor White
Write-Host " 2. Launch Pot-Desktop for Screen OCR & selection translation." -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
