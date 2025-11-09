# Cross-platform PowerShell launcher for gpscentcom_server
# Usage: .\start_centcom.ps1 [console|service] [config_path]

param(
    [string]$Mode = "console",
    [string]$Config = "config.ini"
)

$py = "python"
if ($env:VIRTUAL_ENV) {
    $py = Join-Path $env:VIRTUAL_ENV "Scripts/python.exe"
}

Set-Location $PSScriptRoot

if ($Mode -eq "console") {
    Write-Host "Launching CentCom in CONSOLE mode with $Config"
    & $py -m gpscentcom_server --config $Config
} else {
    Write-Host "Launching CentCom as SERVICE with $Config"
    Start-Process -NoNewWindow -FilePath $py -ArgumentList "-m gpscentcom_server --config $Config" -RedirectStandardOutput "centcom.log" -RedirectStandardError "centcom.log"
    Write-Host "CentCom started as background service. Logs: centcom.log"
}
