param(
    [string]$DocId = 'vv811pxcie8sgs0a0dug1shp',
    [int]$Distance = 277,
    [string]$BaseUrl = 'http://localhost:1337'
)

$payload = @{ data = @{ distance_from_route_m = $Distance } } | ConvertTo-Json -Depth 5
$response = Invoke-RestMethod -Uri "$BaseUrl/api/route-depots/$DocId" -Method PUT -ContentType 'application/json' -Body $payload

if ($null -ne $response.data) {
    $disp = $response.data.display_name
    $distance = $response.data.distance_from_route_m
    Write-Host "Updated route-depot docId=$DocId distance=$distance display_name='$disp'"
} else {
    Write-Host "Response:" ($response | ConvertTo-Json -Depth 5)
}
