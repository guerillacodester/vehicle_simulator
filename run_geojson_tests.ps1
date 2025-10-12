# PowerShell script to run GeoJSON CRUD tests

Write-Host "GeoJSON CRUD Test Suite" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""

# Check if requests is installed
Write-Host "Checking Python dependencies..." -ForegroundColor Yellow
python -c "import requests" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing requests library..." -ForegroundColor Yellow
    pip install requests
}

Write-Host ""
Write-Host "Running tests..." -ForegroundColor Green
Write-Host ""

# Run the test script
python test_geojson_crud.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ All tests passed!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "❌ Tests failed!" -ForegroundColor Red
}

exit $LASTEXITCODE
