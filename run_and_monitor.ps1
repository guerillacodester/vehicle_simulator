# Run the commuter production service and display output
# Press Ctrl+C when you see 16 depot spawns

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "COMMUTER SERVICE - LIVE MONITORING" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Watch for: [DEPOT ] Spawned X passengers" -ForegroundColor Yellow
Write-Host "Target: Stop at 16 depot spawns" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Cyan

Set-Location e:\projects\github\vehicle_simulator
python start_commuter_production.py
