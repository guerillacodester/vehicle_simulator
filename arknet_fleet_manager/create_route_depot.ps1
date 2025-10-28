param(
    [string]$RouteDocId = 'gg3pv3z19hhm117v9xth5ezq',
    [string]$DepotDocId = 'ft3t8jc5jnzg461uod6to898',
    [int]$Distance = 223,
    [string]$BaseUrl = 'http://localhost:1337'
)

$payload = @{
    data = @{
        route = $RouteDocId
        depot = $DepotDocId
        distance_from_route_m = $Distance
        is_start_terminus = $true
    }
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri "$BaseUrl/api/route-depots" -Method POST -ContentType 'application/json' -Body $payload

if ($null -ne $response.data) {
    $id = $response.data.id
    $docId = $response.data.documentId
    $disp = $response.data.display_name
    $routeShort = $response.data.route_short_name
    $depotName = $response.data.depot_name
    
    Write-Host "Created route-depot:"
    Write-Host "  id=$id documentId=$docId"
    Write-Host "  display_name='$disp'"
    Write-Host "  route_short_name='$routeShort'"
    Write-Host "  depot_name='$depotName'"
} else {
    Write-Host "Response:" ($response | ConvertTo-Json -Depth 5)
}
