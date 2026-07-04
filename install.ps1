# voice-pipeline — Installation Script (Windows)
# Run: .\install.ps1

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$BinDir = Join-Path $HOME "voice-pipeline" "bin"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   voice-pipeline — Installation Wizard" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── Check dependencies ────────────────────────────────
Write-Host "Checking dependencies..." -ForegroundColor Yellow

$pythonOk = $false
try {
    $pyVer = python3 --version 2>&1
    Write-Host "  [OK] python3: $pyVer" -ForegroundColor Green
    $pythonOk = $true
} catch {
    try {
        $pyVer = python --version 2>&1
        Write-Host "  [OK] python: $pyVer" -ForegroundColor Green
        $pythonOk = $true
    } catch {
        Write-Host "  [FAIL] python3 not found. Please install Python 3." -ForegroundColor Red
    }
}

$ffplayOk = $false
try {
    $ffVer = ffplay -version 2>&1 | Select-Object -First 1
    Write-Host "  [OK] ffplay: $ffVer" -ForegroundColor Green
    $ffplayOk = $true
} catch {
    Write-Host "  [WARN] ffplay not found (needed for audio playback). Install ffmpeg." -ForegroundColor Yellow
}

if (-not $pythonOk) {
    Write-Host ""
    Write-Host "Python 3 is required. Download from https://www.python.org/" -ForegroundColor Red
    exit 1
}

# ── Create bin directory ───────────────────────────────
Write-Host ""
Write-Host "Installing scripts..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $BinDir | Out-Null

# Create .bat wrapper scripts (Windows doesn't support shebang symlinks)
$batFiles = @{
    "tts-speak.bat"  = "@echo off`r`npython3 `"$ScriptDir\tts_speak.py`" %*"
    "tts-config.bat" = "@echo off`r`npython3 `"$ScriptDir\tts_config.py`" %*"
    "tts-server.bat" = "@echo off`r`npowershell -ExecutionPolicy Bypass -File `"$ScriptDir\tts_server.ps1`" %*"
}

foreach ($name in $batFiles.Keys) {
    $path = Join-Path $BinDir $name
    if (Test-Path $path) {
        Write-Host "  [SKIP] $name already exists" -ForegroundColor Yellow
    } else {
        Set-Content -Path $path -Value $batFiles[$name] -Encoding ASCII
        Write-Host "  [OK] $name -> $BinDir" -ForegroundColor Green
    }
}

# ── Check PATH ─────────────────────────────────────────
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$BinDir*") {
    Write-Host ""
    Write-Host "  [WARN] $BinDir is not in your PATH." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Please add it manually (System Properties > Environment Variables),"
    Write-Host "  or run this command in an Admin PowerShell:"
    Write-Host ""
    Write-Host "    [Environment]::SetEnvironmentVariable('Path', [Environment]::GetEnvironmentVariable('Path', 'User') + ';$BinDir', 'User')"
    Write-Host ""
    Write-Host "  Then restart your terminal."
}

# ── Configuration ──────────────────────────────────────
Write-Host ""
Write-Host "Configuration..." -ForegroundColor Yellow

$ConfigDir = Join-Path $HOME ".voice_pipeline"
if (Test-Path (Join-Path $ConfigDir "config.json")) {
    Write-Host "  [SKIP] Config already exists: $ConfigDir\config.json" -ForegroundColor Yellow
} else {
    Write-Host "  [INFO] First time setup — configure with:" -ForegroundColor Cyan
    Write-Host "     tts-config"
    Write-Host "     tts-config --ref-dir \path\to\ref_audio"
    Write-Host "     tts-config --ref-audio reference.wav"
    Write-Host "     tts-config --prompt 'reference text' ja"
}

# ── Git submodule ──────────────────────────────────────
Write-Host ""
Write-Host "GPT-SoVITS submodule..." -ForegroundColor Yellow

Push-Location $ScriptDir
try {
    $subStatus = git submodule status 2>&1
    if ($subStatus -match "^-") {
        Write-Host "  [WARN] Submodule not initialized. Run:" -ForegroundColor Yellow
        Write-Host "     cd $ScriptDir"
        Write-Host "     git submodule update --init --recursive"
    } else {
        Write-Host "  [OK] Submodule ready" -ForegroundColor Green
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  Installation complete!" -ForegroundColor Green
Write-Host ""
Write-Host "  Quick start:"
Write-Host "    1. Configure inference: tts-config --infer-auto"
Write-Host "    2. Configure client: tts-config"
Write-Host "    3. Start service: tts-server"
Write-Host "    4. Test: tts-speak 'konnichiwa' ja"
Write-Host "============================================" -ForegroundColor Cyan
