# voice-pipeline — GPT-SoVITS API Service Management (Windows)
# Usage:
#   .\tts_server.ps1             # Check status, auto-start if not running
#   .\tts_server.ps1 -Mode on    # Start service
#   .\tts_server.ps1 -Mode off   # Stop service
#   .\tts_server.ps1 -Mode status # Show status only

param(
    [Parameter(Position = 0)]
    [ValidateSet("auto", "on", "off", "start", "stop", "status")]
    [string]$Mode = "auto"
)

$ErrorActionPreference = "Stop"

# ── Configuration ──────────────────────────────────────
$Port = if ($env:VOICE_PIPELINE_PORT) { [int]$env:VOICE_PIPELINE_PORT } else { 9880 }
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = if ($env:VOICE_PIPELINE_PROJECT_DIR) { $env:VOICE_PIPELINE_PROJECT_DIR } else { Join-Path $ScriptDir "GPT-SoVITS" }
$CondaEnv = if ($env:VOICE_PIPELINE_CONDA) { $env:VOICE_PIPELINE_CONDA } else { "GPTSoVits" }
$ConfigFile = if ($env:VOICE_PIPELINE_CONFIG) { $env:VOICE_PIPELINE_CONFIG } else { Join-Path $ScriptDir "tts_infer.yaml" }
$PidFile = Join-Path $env:TEMP "voice_pipeline_server.pid"
$LogFile = Join-Path $env:TEMP "voice_pipeline_server.log"

# ── Helpers ───────────────────────────────────────────

function Get-ServerPid {
    try {
        $conn = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($conn) { return $conn.OwningProcess }
    } catch {
        # Fallback: netstat
        $line = netstat -ano 2>$null | Select-String ":$Port " | Select-Object -First 1
        if ($line) {
            $parts = $line.ToString().TrimEnd() -split '\s+'
            $pidStr = $parts[-1]
            if ($pidStr -match '^\d+$') { return [int]$pidStr }
        }
    }
    return $null
}

function Test-ServerRunning {
    $pid = Get-ServerPid
    return ($null -ne $pid)
}

function Show-Status {
    $pid = Get-ServerPid
    if ($pid) {
        Write-Host "[OK] TTS service is running" -ForegroundColor Green
        Write-Host "   PID:      $pid"
        Write-Host "   Address:  http://127.0.0.1:$Port"
        Write-Host "   Project:  $ProjectDir"
        Write-Host "   Log:      $LogFile"
        Write-Host "   Conda:    $CondaEnv"
    } else {
        Write-Host "[OFF] TTS service is not running" -ForegroundColor Red
        Write-Host "   Port:     $Port"
        Write-Host "   Project:  $ProjectDir"
    }
}

# ── Start ─────────────────────────────────────────────

function Start-Server {
    if (Test-ServerRunning) {
        Write-Host "[WARN] Service already running, skipping" -ForegroundColor Yellow
        return
    }

    if (-not (Test-Path $ConfigFile)) {
        Write-Host "[ERROR] Config file not found: $ConfigFile" -ForegroundColor Red
        Write-Host "   Copy and modify from tts_infer.yaml.example"
        throw "Config not found"
    }

    Write-Host -NoNewline "Starting TTS service... "

    $proc = Start-Process -FilePath "conda" `
        -ArgumentList "run", "-n", $CondaEnv, "--no-capture-output", "python", "api_v2.py", "-a", "0.0.0.0", "-p", "$Port", "-c", "$ConfigFile" `
        -WorkingDirectory $ProjectDir `
        -NoNewWindow `
        -RedirectStandardOutput $LogFile `
        -RedirectStandardError $LogFile `
        -PassThru

    $proc.Id | Out-File -FilePath $PidFile -Encoding ASCII

    $waited = 0
    while (-not (Test-ServerRunning) -and $waited -lt 40) {
        Start-Sleep -Seconds 1
        $waited++
    }

    if (Test-ServerRunning) {
        Write-Host "Done" -ForegroundColor Green
    } else {
        Write-Host "Timeout" -ForegroundColor Red
        Write-Host "  Check log: gc $LogFile"
        throw "Start timeout"
    }
}

# ── Stop ──────────────────────────────────────────────

function Stop-Server {
    if (-not (Test-ServerRunning)) {
        Write-Host "[WARN] Service not running" -ForegroundColor Yellow
        return
    }

    $pid = Get-ServerPid
    Write-Host -NoNewline "Stopping TTS service (PID: $pid)... "
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue

    $waited = 0
    while (Test-ServerRunning -and $waited -lt 10) {
        Start-Sleep -Seconds 1
        $waited++
    }

    if (-not (Test-ServerRunning)) {
        Write-Host "Done" -ForegroundColor Green
        Remove-Item $PidFile -ErrorAction SilentlyContinue
    } else {
        Write-Host "Force killing..." -ForegroundColor Yellow
        Stop-Process -Id $pid -Force
        Start-Sleep -Seconds 1
        Remove-Item $PidFile -ErrorAction SilentlyContinue
        Write-Host "Done" -ForegroundColor Green
    }
}

# ── Entry ─────────────────────────────────────────────

switch ($Mode) {
    "on"    { Start-Server }
    "start" { Start-Server }
    "off"   { Stop-Server }
    "stop"  { Stop-Server }
    "status"{ Show-Status; return }
    "auto"  {
        if (-not (Test-ServerRunning)) {
            Write-Host "Service not running, auto-starting..." -ForegroundColor Yellow
            Start-Server
        }
    }
}

Write-Host ""
Show-Status
