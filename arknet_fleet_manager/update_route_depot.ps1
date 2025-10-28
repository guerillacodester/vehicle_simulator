param(
    [int]$Id = 7,
    [int]$Distance = 223,
    [string]$BaseUrl = 'http://localhost:1337'
)

$payload = @{ data = @{ distance_from_route_m = $Distance } } | ConvertTo-Json -Depth 5
$response = Invoke-RestMethod -Uri "$BaseUrl/api/route-depots/$Id" -Method PUT -ContentType 'application/json' -Body $payload

if ($null -ne $response.data) {
    $disp = $response.data.attributes.display_name
    Write-Host "Updated route-depot id=$Id display_name=$disp"
} else {
    Write-Host "Response:" ($response | ConvertTo-Json -Depth 5)
}
