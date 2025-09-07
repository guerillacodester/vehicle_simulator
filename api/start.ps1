#!/usr/bin/env pwsh
# Fleet Management API Starter Script
# Run with: .\start.ps1 or just .\start

Write-Host "🚀 Starting Fleet Management API..." -ForegroundColor Green

try {
    # Change to the script directory
    $ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    Set-Location $ScriptDir
    
    # Start the API server
    py main.py
}
catch {
    Write-Host "❌ Error starting server: $_" -ForegroundColor Red
    Write-Host "💡 Try running: py main.py" -ForegroundColor Yellow
}
finally {
    Write-Host "🛑 Server stopped" -ForegroundColor Red
}
