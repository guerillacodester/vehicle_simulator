# ArkNet Host Server - Start All Services (Windows)
# This script starts the Host Server which manages all subservices

param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 6000
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$VenvPath = Join-Path $ProjectRoot "venv"
$PythonExe = Join-Path $VenvPath "Scripts\python.exe"
$LogDir = Join-Path $ProjectRoot "logs"
$PidFile = Join-Path $ProjectRoot ".host_server.pid"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ArkNet Host Server Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check if already running
if (Test-Path $PidFile) {
    $PID = Get-Content $PidFile
    if (Get-Process -Id $PID -ErrorAction SilentlyContinue) {
        Write-Host "⚠️  Host Server already running (PID: $PID)" -ForegroundColor Yellow
        Write-Host "   Use stop_all.ps1 to stop it first" -ForegroundColor Yellow
        exit 1
    } else {
        Write-Host "⚠️  Stale PID file found, removing..." -ForegroundColor Yellow
        Remove-Item $PidFile
    }
}

# Create log directory
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir | Out-Null
}

# Check Python venv
if (-not (Test-Path $PythonExe)) {
    Write-Host "❌ Python virtualenv not found at: $VenvPath" -ForegroundColor Red
    Write-Host "   Run: python -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Check dependencies
Write-Host "🔍 Checking dependencies..." -ForegroundColor Cyan
try {
    & $PythonExe -c "import fastapi, uvicorn, httpx" 2>$null
    Write-Host "✅ Dependencies OK" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Missing dependencies, installing..." -ForegroundColor Yellow
    & (Join-Path $VenvPath "Scripts\pip.exe") install -q fastapi uvicorn httpx
}

# Start Host Server in background
Write-Host "🚀 Starting Host Server..." -ForegroundColor Cyan
Set-Location $ProjectRoot

$LogFile = Join-Path $LogDir "host_server.log"

$ProcessArgs = @{
    FilePath = $PythonExe
    ArgumentList = "-m", "services.host_server", "--host", $Host, "--port", $Port
    RedirectStandardOutput = $LogFile
    RedirectStandardError = $LogFile
    NoNewWindow = $true
    PassThru = $true
}

$Process = Start-Process @ProcessArgs
$Process.Id | Set-Content $PidFile

# Wait for startup
Write-Host "⏳ Waiting for Host Server to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Check if process is running
if (Get-Process -Id $Process.Id -ErrorAction SilentlyContinue) {
    Write-Host "✅ Host Server started successfully!" -ForegroundColor Green
    Write-Host "   PID:     $($Process.Id)" -ForegroundColor Green
    Write-Host "   URL:     http://localhost:$Port" -ForegroundColor Green
    Write-Host "   Health:  http://localhost:$Port/health" -ForegroundColor Green
    Write-Host "   Logs:    Get-Content -Wait $LogFile" -ForegroundColor Green
    Write-Host ""
    Write-Host "📋 Next Steps:" -ForegroundColor Cyan
    Write-Host "   1. Start simulator:  Invoke-WebRequest -Method POST http://localhost:$Port/api/services/simulator/start" -ForegroundColor Cyan
    Write-Host "   2. Connect console:  python -m clients.fleet" -ForegroundColor Cyan
    Write-Host "   3. Check services:   services" -ForegroundColor Cyan
} else {
    Write-Host "❌ Failed to start Host Server" -ForegroundColor Red
    Write-Host "   Check logs: $LogFile" -ForegroundColor Red
    Remove-Item $PidFile
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
