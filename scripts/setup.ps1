<#
.SYNOPSIS
    Universal 1-Click Setup Script for Real-Time Audio & Text Translation Hub.
.DESCRIPTION
    Installs and configures Pot-Desktop (OCR / Screen translator) and downloads
    LiveCaptions-Translator (Audio / Subtitles) with compact keyboard presets.
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
$ConfigsDir = Join-Path $WorkspaceRoot "configs"

if (-not (Test-Path $BinDir)) {
    New-Item -ItemType Directory -Path $BinDir -Force | Out-Null
    Write-Host "[+] Created local binary directory: $BinDir" -ForegroundColor Green
}

# 1. Check Winget and Install Pot-Desktop
Write-Host "`n[Step 1/3] Checking Pot-Desktop (Screen OCR & Text Translator)..." -ForegroundColor Yellow
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
            Write-Warning "  -> Winget auto-install failed. You can manually download Pot from: https://github.com/pot-app/pot-desktop/releases"
        }
    }
}

# 2. Download LiveCaptions-Translator
Write-Host "`n[Step 2/3] Checking LiveCaptions-Translator (System Audio & Subtitles)..." -ForegroundColor Yellow
$liveCaptionsExe = Join-Path $BinDir "LiveCaptionsTranslator.exe"

if (Test-Path $liveCaptionsExe) {
    Write-Host "  -> LiveCaptions-Translator executable is already present in bin/" -ForegroundColor Green
} else {
    Write-Host "  -> Downloading latest standalone LiveCaptions-Translator (with runtime)..." -ForegroundColor Cyan
    $downloadUrl = "https://github.com/SakiRinn/LiveCaptions-Translator/releases/latest/download/LiveCaptionsTranslator-win-x64-withruntime.exe"
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $liveCaptionsExe -UseBasicParsing
        Write-Host "  -> Downloaded successfully to: $liveCaptionsExe" -ForegroundColor Green
    } catch {
        Write-Warning "  -> Automatic download could not reach GitHub. Manual download link: https://github.com/SakiRinn/LiveCaptions-Translator/releases/latest"
    }
}

# 3. Deploy Template Settings
Write-Host "`n[Step 3/3] Setting up configuration templates..." -ForegroundColor Yellow
$localLiveCaptionsConfig = Join-Path $BinDir "setting.json"
$templateLiveCaptionsConfig = Join-Path $ConfigsDir "livecaptions-translator\setting.template.json"

if (-not (Test-Path $localLiveCaptionsConfig) -and (Test-Path $templateLiveCaptionsConfig)) {
    Copy-Item $templateLiveCaptionsConfig -Destination $localLiveCaptionsConfig
    Write-Host "  -> Created initial configuration: $localLiveCaptionsConfig" -ForegroundColor Green
    Write-Host "  -> Preset loaded: Russian target language + Educational Prompting (💡 vocabulary hints)." -ForegroundColor Magenta
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Setup complete! Quick Start Checklist:" -ForegroundColor Green
Write-Host " 1. Press [Win + Ctrl + L] to start Windows Live Captions." -ForegroundColor White
Write-Host "    - Set Caption Language to English (United States)." -ForegroundColor White
Write-Host " 2. Run: $liveCaptionsExe" -ForegroundColor White
Write-Host "    - Add your translation API key (DeepSeek or OpenAI) in Settings." -ForegroundColor White
Write-Host " 3. Launch Pot-Desktop:" -ForegroundColor White
Write-Host "    - Press [Alt + Q] to snip and translate any on-screen text." -ForegroundColor White
Write-Host "    - Press [Alt + W] to translate highlighted text anywhere." -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
