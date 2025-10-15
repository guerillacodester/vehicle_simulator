@echo off
echo Cleaning Strapi cache and rebuilding...
cd arknet_fleet_manager\arknet-fleet-api

echo.
echo 1. Stopping Strapi (if running)...
timeout /t 2 /nobreak >nul

echo.
echo 2. Removing build cache...
if exist .cache rd /s /q .cache
if exist build rd /s /q build
if exist .tmp rd /s /q .tmp

echo.
echo 3. Rebuilding Strapi...
call npm run build

echo.
echo 4. Starting Strapi in development mode...
echo    (This will load the new content type)
call npm run develop
