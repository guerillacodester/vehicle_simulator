# Fetch route geometry from API
$response = Invoke-WebRequest -Uri "http://localhost:1337/api/routes/1/geometry" -Method GET
$data = $response.Content | ConvertFrom-Json

Write-Host "`n=== Distance Computation from API Output ===" -ForegroundColor Green
Write-Host "Route: $($data.routeName)"
Write-Host "Coordinates: $($data.coordinateCount)"
Write-Host "Segments: $($data.segmentCount)"
Write-Host "`nAPI Reported Distance: $($data.distanceKm) km"
Write-Host "API Metrics Distance: $($data.metrics.estimatedLengthKm) km"

# Haversine formula
function Get-HaversineDistance {
    param($lat1, $lon1, $lat2, $lon2)
    $R = 6371  # Earth radius in km
    $dLat = ($lat2 - $lat1) * [Math]::PI / 180
    $dLon = ($lon2 - $lon1) * [Math]::PI / 180
    $a = [Math]::Sin($dLat/2) * [Math]::Sin($dLat/2) + 
         [Math]::Cos($lat1 * [Math]::PI / 180) * [Math]::Cos($lat2 * [Math]::PI / 180) *
         [Math]::Sin($dLon/2) * [Math]::Sin($dLon/2)
    $c = 2 * [Math]::Atan2([Math]::Sqrt($a), [Math]::Sqrt(1-$a))
    return $R * $c
}

# Calculate total distance
$totalDistance = 0
for ($i = 0; $i -lt ($data.coordinates.Count - 1); $i++) {
    $lon1 = [double]$data.coordinates[$i][0]
    $lat1 = [double]$data.coordinates[$i][1]
    $lon2 = [double]$data.coordinates[$i + 1][0]
    $lat2 = [double]$data.coordinates[$i + 1][1]
    $segmentDist = Get-HaversineDistance $lat1 $lon1 $lat2 $lon2
    $totalDistance += $segmentDist
}

Write-Host "`nComputed Distance (Haversine): $([Math]::Round($totalDistance, 6)) km" -ForegroundColor Cyan
Write-Host "Difference: $([Math]::Round([Math]::Abs($totalDistance - $data.distanceKm), 6)) km"
Write-Host "Match: $([Math]::Round(($totalDistance / $data.distanceKm) * 100, 2))%" -ForegroundColor Yellow
