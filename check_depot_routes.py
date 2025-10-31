import requests

STRAPI_URL = "http://localhost:1337"

# Get all depots
depots_response = requests.get(f"{STRAPI_URL}/api/depots?pagination[pageSize]=100")
depots = depots_response.json()['data']

print("=" * 80)
print("DEPOT-ROUTE ASSOCIATIONS")
print("=" * 80)

for depot in depots:
    depot_id = depot['id']
    depot_doc_id = depot['documentId']
    depot_name = depot['name']
    
    print(f"\n{'='*80}")
    print(f"Depot: {depot_name}")
    print(f"  ID: {depot_id}")
    print(f"  DocumentID: {depot_doc_id}")
    
    # Query route-depots table for this depot
    route_depots_response = requests.get(
        f"{STRAPI_URL}/api/route-depots",
        params={
            "filters[depot][documentId][$eq]": depot_doc_id,
            "populate": "route",
            "pagination[pageSize]": 100
        }
    )
    
    route_depots = route_depots_response.json()['data']
    
    if route_depots:
        print(f"  ✅ Associated Routes ({len(route_depots)}):")
        for rd in route_depots:
            route = rd.get('route')
            if route:
                print(f"     - Route {route.get('route_short_name')} (documentId: {route.get('documentId')})")
                print(f"       Distance: {rd.get('distance_from_route_m', 'N/A')}m")
                print(f"       Start terminus: {rd.get('is_start_terminus', False)}")
                print(f"       End terminus: {rd.get('is_end_terminus', False)}")
            else:
                print(f"     - Route data missing in response")
    else:
        print(f"  ❌ NO ROUTES ASSOCIATED")

print("\n" + "=" * 80)
print("ROUTE-DEPOT ASSOCIATIONS (REVERSE CHECK)")
print("=" * 80)

# Get all routes
routes_response = requests.get(f"{STRAPI_URL}/api/routes?pagination[pageSize]=100")
routes = routes_response.json()['data']

for route in routes:
    route_id = route['id']
    route_doc_id = route['documentId']
    route_name = route.get('route_short_name', 'Unknown')
    
    print(f"\n{'='*80}")
    print(f"Route: {route_name}")
    print(f"  ID: {route_id}")
    print(f"  DocumentID: {route_doc_id}")
    
    # Query route-depots table for this route
    route_depots_response = requests.get(
        f"{STRAPI_URL}/api/route-depots",
        params={
            "filters[route][documentId][$eq]": route_doc_id,
            "populate": "depot",
            "pagination[pageSize]": 100
        }
    )
    
    route_depots = route_depots_response.json()['data']
    
    if route_depots:
        print(f"  ✅ Associated Depots ({len(route_depots)}):")
        for rd in route_depots:
            depot = rd.get('depot')
            if depot:
                print(f"     - {depot.get('name')} (documentId: {depot.get('documentId')})")
                print(f"       Distance: {rd.get('distance_from_route_m', 'N/A')}m")
                print(f"       Start terminus: {rd.get('is_start_terminus', False)}")
                print(f"       End terminus: {rd.get('is_end_terminus', False)}")
            else:
                print(f"     - Depot data missing in response")
    else:
        print(f"  ❌ NO DEPOTS ASSOCIATED")
