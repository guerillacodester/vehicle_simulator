# ArkNet Fleet Manager - Production Startup Script
# Run this to start both Strapi backend and Next.js dashboard

Write-Host "🚀 Starting ArkNet Fleet Manager..." -ForegroundColor Cyan
Write-Host ""

# Check if Strapi is already running
$strapiPort = netstat -ano | findstr ":1337.*LISTENING"
if ($strapiPort) {
    Write-Host "✅ Strapi backend is already running on port 1337" -ForegroundColor Green
} else {
    Write-Host "⚠️  Strapi backend is not running!" -ForegroundColor Yellow
    Write-Host "Starting Strapi backend..." -ForegroundColor Yellow
    
    # Start Strapi in a new terminal
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\arknet_fleet_manager\arknet-fleet-api'; npm run develop"
    
    Write-Host "⏳ Waiting for Strapi to start (15 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
}

Write-Host ""
Write-Host "📊 Starting Next.js Dashboard..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will be available at: http://localhost:3000" -ForegroundColor Green
Write-Host "Strapi Admin Panel: http://localhost:1337/admin" -ForegroundColor Green
Write-Host ""

# Start Next.js dashboard
cd "$PSScriptRoot\arknet_fleet_manager\dashboard"
npm run dev
