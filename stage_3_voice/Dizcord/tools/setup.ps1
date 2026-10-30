# Builds / repairs the portable runtime inside the app folder:
#   runtime\          private Python (embeddable distribution) + all packages
# Nothing is installed system-wide and no admin rights are needed.
param(
    [string]$PythonVersion = "3.13.16",
    [string]$Requirements = "requirements.txt",
    [string[]]$Packages = @()
)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$Root = Split-Path -Parent $PSScriptRoot
$Rt = Join-Path $Root "runtime"
$Py = Join-Path $Rt "python.exe"
$Tmp = Join-Path $Rt "_tmp"
New-Item -ItemType Directory -Force $Tmp | Out-Null
$env:TEMP = $Tmp; $env:TMP = $Tmp
$env:PIP_DISABLE_PIP_VERSION_CHECK = "1"
$env:PIP_CACHE_DIR = Join-Path $Tmp "pip-cache"        # keep pip's download cache inside the app folder too (deleted at the end)
$env:PYTHONNOUSERSITE = "1"

function Step($msg) { Write-Host ""; Write-Host "==> $msg" -ForegroundColor Cyan }

if (-not (Test-Path $Py)) {
    Step "Downloading portable Python $PythonVersion"
    $zip = Join-Path $Tmp "python.zip"
    $url = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-embed-amd64.zip"
    Invoke-WebRequest -Uri $url -OutFile $zip -UseBasicParsing
    Expand-Archive -Path $zip -DestinationPath $Rt -Force
    Remove-Item $zip
    # Enable site-packages and let Python see the app folder.
    $pth = Get-ChildItem $Rt -Filter "python*._pth" | Select-Object -First 1
    $zipName = (Get-ChildItem $Rt -Filter "python*.zip" | Select-Object -First 1).Name
    Set-Content -Path $pth.FullName -Encoding ascii -Value @($zipName, ".", "Lib\site-packages", "..", "import site")
}

if (-not (Test-Path (Join-Path $Rt "Lib\site-packages\pip"))) {
    Step "Installing pip"
    $gp = Join-Path $Tmp "get-pip.py"
    Invoke-WebRequest -Uri "https://bootstrap.pypa.io/get-pip.py" -OutFile $gp -UseBasicParsing
    & $Py $gp --no-warn-script-location
    if ($LASTEXITCODE -ne 0) { throw "pip installation failed" }
}

# The embeddable Python ignores PYTHONPATH (python313._pth), so pip's isolated build environments cannot work:
# a package published only as source (e.g. langdetect) fails with "Cannot import 'setuptools.build_meta'".
# Install the build tools into the runtime itself and build without isolation.
$Ready = Join-Path $Rt ".setup-ok"                       # written last: the launchers re-run setup until it exists
Remove-Item $Ready -ErrorAction SilentlyContinue
Step "Installing build tools"
& $Py -m pip install --no-warn-script-location --upgrade setuptools wheel
if ($LASTEXITCODE -ne 0) { throw "Build tools installation failed (see messages above)" }

$Packages = @($Packages | ForEach-Object { $_ -split "," } | Where-Object { $_ })
if ($Packages.Count -gt 0) {
    Step "Installing $($Packages -join ', ')"
    & $Py -m pip install --no-warn-script-location --no-build-isolation @Packages
} else {
    Step "Installing app packages (first time takes a few minutes)"
    & $Py -m pip install --no-warn-script-location --no-build-isolation -r (Join-Path $Root $Requirements)
}
if ($LASTEXITCODE -ne 0) { throw "Package installation failed (see messages above)" }

# Offline natural voice for the Manual (Piper, ~60 MB). Saved inside the app folder (models\piper), once.
if ($Packages.Count -eq 0) {
    $PiperDir = Join-Path $Root "models\piper"
    $Voice = "en_US-kristin-medium"
    if (-not (Test-Path (Join-Path $PiperDir "$Voice.onnx.json"))) {
        Step "Downloading the offline voice for the Manual (~60 MB, once)"
        try {
            New-Item -ItemType Directory -Force $PiperDir | Out-Null
            $base = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/kristin/medium/$Voice"
            Invoke-WebRequest -Uri "$base.onnx" -OutFile (Join-Path $PiperDir "$Voice.onnx") -UseBasicParsing
            Invoke-WebRequest -Uri "$base.onnx.json" -OutFile (Join-Path $PiperDir "$Voice.onnx.json") -UseBasicParsing
        } catch {
            # not fatal: the Manual falls back to the online / Windows voice. Run setup.bat again to retry.
            Remove-Item (Join-Path $PiperDir "$Voice.onnx*") -ErrorAction SilentlyContinue
            Write-Host "Could not download the offline voice ($($_.Exception.Message)). Run setup.bat again later." -ForegroundColor Yellow
        }
    }
}

Remove-Item -Recurse -Force $Tmp -ErrorAction SilentlyContinue
Set-Content -Path $Ready -Encoding ascii -Value "ok"
Step "Done. Start the app with Dizcord.bat"
