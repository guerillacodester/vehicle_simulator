# Fleet Management Console Launcher
# Quick launcher for the Fleet Management Console

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " ArkNet Fleet Management Console" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if simulator is running
Write-Host "Checking if Fleet API is available..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:5001/health" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Fleet API is running" -ForegroundColor Green
    Write-Host "   Simulator: $($response.simulator_running)" -ForegroundColor White
    Write-Host "   Vehicles:  $($response.active_vehicles)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ Fleet API not available" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start the simulator first:" -ForegroundColor Yellow
    Write-Host "  python -m arknet_transit_simulator --mode depot" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit 1
    }
}

# Launch console
Write-Host "Launching Fleet Console..." -ForegroundColor Cyan
Write-Host ""
python -m clients.fleet
