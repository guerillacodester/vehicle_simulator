"""
Search router for Fleet Management API - Human-readable results only
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import text, or_, and_
from typing import List, Optional

from ..dependencies import get_db
from ..schemas.search_results import VehicleSearchResult, DriverSearchResult, VehicleDriverPair

router = APIRouter(
    prefix="/search",
    tags=["search"],
    responses={404: {"description": "Not found"}},
)

@router.get("/vehicles", response_model=List[VehicleSearchResult])
def search_vehicles(
    registration: Optional[str] = Query(None, description="Search by registration/license plate (partial match)"),
    driver_name: Optional[str] = Query(None, description="Search by assigned driver name (partial match)"),
    driver_license: Optional[str] = Query(None, description="Search by driver license number (exact match)"),
    route_code: Optional[str] = Query(None, description="Search by route code/number (partial match)"),
    status: Optional[str] = Query(None, description="Filter by vehicle status"),
    depot_name: Optional[str] = Query(None, description="Search by depot name (partial match)"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for vehicles using human-readable criteria.
    Returns vehicle information with names instead of UUIDs.
    """
    
    # Build the query with joins for human-readable data
    query = text("""
        SELECT 
            v.reg_code as registration,
            v.status,
            v.capacity,
            d.name as assigned_driver_name,
            d.license_no as assigned_driver_license,
            r.short_name as assigned_route_code,
            r.long_name as assigned_route_name,
            depot.name as home_depot_name,
            v.profile_id,
            v.notes,
            v.created_at,
            v.updated_at
        FROM vehicles v
        LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
        LEFT JOIN routes r ON v.preferred_route_id = r.route_id
        LEFT JOIN depots depot ON v.home_depot_id = depot.depot_id
        WHERE 1=1
        """ + 
        (" AND LOWER(v.reg_code) LIKE LOWER(:registration)" if registration else "") +
        (" AND LOWER(d.name) LIKE LOWER(:driver_name)" if driver_name else "") +
        (" AND d.license_no = :driver_license" if driver_license else "") +
        (" AND (LOWER(r.short_name) LIKE LOWER(:route_code) OR LOWER(r.long_name) LIKE LOWER(:route_code))" if route_code else "") +
        (" AND LOWER(v.status) = LOWER(:status)" if status else "") +
        (" AND LOWER(depot.name) LIKE LOWER(:depot_name)" if depot_name else "") +
        " ORDER BY v.reg_code LIMIT :limit"
    )
    
    # Build parameters dictionary
    params = {"limit": limit}
    if registration:
        params["registration"] = f"%{registration}%"
    if driver_name:
        params["driver_name"] = f"%{driver_name}%"
    if driver_license:
        params["driver_license"] = driver_license
    if route_code:
        params["route_code"] = f"%{route_code}%"
    if status:
        params["status"] = status
    if depot_name:
        params["depot_name"] = f"%{depot_name}%"
    
    result = db.execute(query, params)
    vehicles = result.fetchall()
    
    if not vehicles:
        return []
    
    return [
        VehicleSearchResult(
            registration=v.registration,
            status=v.status,
            capacity=v.capacity,
            assigned_driver_name=v.assigned_driver_name,
            assigned_driver_license=v.assigned_driver_license,
            assigned_route_code=v.assigned_route_code,
            assigned_route_name=v.assigned_route_name,
            home_depot_name=v.home_depot_name,
            profile_id=v.profile_id,
            notes=v.notes,
            created_at=v.created_at,
            updated_at=v.updated_at
        )
        for v in vehicles
    ]

@router.get("/drivers", response_model=List[DriverSearchResult])
def search_drivers(
    name: Optional[str] = Query(None, description="Search by driver name (partial match)"),
    license_number: Optional[str] = Query(None, description="Search by license number (exact match)"),
    depot_name: Optional[str] = Query(None, description="Search by depot name (partial match)"),
    employment_status: Optional[str] = Query(None, description="Filter by employment status"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for drivers using human-readable criteria.
    Returns driver information with names instead of UUIDs, including assigned vehicles.
    """
    
    # First get the driver information
    query = text("""
        SELECT 
            d.driver_id,
            d.name,
            d.license_no as license_number,
            d.employment_status,
            depot.name as home_depot_name,
            d.created_at,
            d.updated_at
        FROM drivers d
        LEFT JOIN depots depot ON d.home_depot_id = depot.depot_id
        WHERE 1=1
        """ + 
        (" AND LOWER(d.name) LIKE LOWER(:name)" if name else "") +
        (" AND d.license_no = :license_number" if license_number else "") +
        (" AND LOWER(depot.name) LIKE LOWER(:depot_name)" if depot_name else "") +
        (" AND LOWER(d.employment_status) = LOWER(:employment_status)" if employment_status else "") +
        " ORDER BY d.name LIMIT :limit"
    )
    
    # Build parameters dictionary
    params = {"limit": limit}
    if name:
        params["name"] = f"%{name}%"
    if license_number:
        params["license_number"] = license_number
    if depot_name:
        params["depot_name"] = f"%{depot_name}%"
    if employment_status:
        params["employment_status"] = employment_status
    
    result = db.execute(query, params)
    drivers = result.fetchall()
    
    if not drivers:
        return []
    
    # Get assigned vehicles for each driver
    driver_results = []
    for driver in drivers:
        # Get vehicles assigned to this driver
        vehicle_query = text("""
            SELECT reg_code 
            FROM vehicles 
            WHERE assigned_driver_id = :driver_id
            ORDER BY reg_code
        """)
        
        vehicle_result = db.execute(vehicle_query, {"driver_id": driver.driver_id})
        assigned_vehicles = [v.reg_code for v in vehicle_result.fetchall()]
        
        driver_results.append(
            DriverSearchResult(
                name=driver.name,
                license_number=driver.license_number,
                employment_status=driver.employment_status,
                assigned_vehicles=assigned_vehicles,
                home_depot_name=driver.home_depot_name,
                created_at=driver.created_at,
                updated_at=driver.updated_at
            )
        )
    
    return driver_results

@router.get("/vehicle-driver-pairs", response_model=List[VehicleDriverPair])
def search_vehicle_driver_pairs(
    registration: Optional[str] = Query(None, description="Search by vehicle registration (partial match)"),
    driver_name: Optional[str] = Query(None, description="Search by driver name (partial match)"),
    route_code: Optional[str] = Query(None, description="Search by route code (partial match)"),
    depot_name: Optional[str] = Query(None, description="Search by depot name (partial match)"),
    limit: int = Query(50, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Search for vehicle-driver pairs with complete relationship information.
    Only returns vehicles that have assigned drivers.
    """
    
    query = text("""
        SELECT 
            v.reg_code as registration,
            v.status as vehicle_status,
            v.capacity as vehicle_capacity,
            d.name as driver_name,
            d.license_no as driver_license,
            d.employment_status as driver_employment_status,
            r.short_name as route_code,
            r.long_name as route_name,
            depot.name as depot_name,
            v.updated_at as assignment_date
        FROM vehicles v
        INNER JOIN drivers d ON v.assigned_driver_id = d.driver_id
        LEFT JOIN routes r ON v.preferred_route_id = r.route_id
        LEFT JOIN depots depot ON v.home_depot_id = depot.depot_id
        WHERE 1=1
        """ + 
        (" AND LOWER(v.reg_code) LIKE LOWER(:registration)" if registration else "") +
        (" AND LOWER(d.name) LIKE LOWER(:driver_name)" if driver_name else "") +
        (" AND (LOWER(r.short_name) LIKE LOWER(:route_code) OR LOWER(r.long_name) LIKE LOWER(:route_code))" if route_code else "") +
        (" AND LOWER(depot.name) LIKE LOWER(:depot_name)" if depot_name else "") +
        " ORDER BY v.reg_code LIMIT :limit"
    )
    
    # Build parameters dictionary
    params = {"limit": limit}
    if registration:
        params["registration"] = f"%{registration}%"
    if driver_name:
        params["driver_name"] = f"%{driver_name}%"
    if route_code:
        params["route_code"] = f"%{route_code}%"
    if depot_name:
        params["depot_name"] = f"%{depot_name}%"
    
    result = db.execute(query, params)
    pairs = result.fetchall()
    
    if not pairs:
        return []
    
    return [
        VehicleDriverPair(
            registration=pair.registration,
            vehicle_status=pair.vehicle_status,
            vehicle_capacity=pair.vehicle_capacity,
            driver_name=pair.driver_name,
            driver_license=pair.driver_license,
            driver_employment_status=pair.driver_employment_status,
            route_code=pair.route_code,
            route_name=pair.route_name,
            depot_name=pair.depot_name,
            assignment_date=pair.assignment_date
        )
        for pair in pairs
    ]

@router.get("/vehicles/by-registration/{registration}", response_model=VehicleSearchResult)
def get_vehicle_by_registration(
    registration: str,
    db: Session = Depends(get_db)
):
    """Get a single vehicle by exact registration match with human-readable information."""
    
    query = text("""
        SELECT 
            v.reg_code as registration,
            v.status,
            v.capacity,
            d.name as assigned_driver_name,
            d.license_no as assigned_driver_license,
            r.short_name as assigned_route_code,
            r.long_name as assigned_route_name,
            depot.name as home_depot_name,
            v.profile_id,
            v.notes,
            v.created_at,
            v.updated_at
        FROM vehicles v
        LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
        LEFT JOIN routes r ON v.preferred_route_id = r.route_id
        LEFT JOIN depots depot ON v.home_depot_id = depot.depot_id
        WHERE LOWER(v.reg_code) = LOWER(:registration)
    """)
    
    result = db.execute(query, {"registration": registration})
    vehicle = result.fetchone()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail=f"Vehicle with registration '{registration}' not found")
    
    return VehicleSearchResult(
        registration=vehicle.registration,
        status=vehicle.status,
        capacity=vehicle.capacity,
        assigned_driver_name=vehicle.assigned_driver_name,
        assigned_driver_license=vehicle.assigned_driver_license,
        assigned_route_code=vehicle.assigned_route_code,
        assigned_route_name=vehicle.assigned_route_name,
        home_depot_name=vehicle.home_depot_name,
        profile_id=vehicle.profile_id,
        notes=vehicle.notes,
        created_at=vehicle.created_at,
        updated_at=vehicle.updated_at
    )

@router.get("/drivers/by-license/{license_number}", response_model=DriverSearchResult)
def get_driver_by_license(
    license_number: str,
    db: Session = Depends(get_db)
):
    """Get a single driver by exact license number match with human-readable information."""
    
    # Get driver information
    query = text("""
        SELECT 
            d.driver_id,
            d.name,
            d.license_no as license_number,
            d.employment_status,
            depot.name as home_depot_name,
            d.created_at,
            d.updated_at
        FROM drivers d
        LEFT JOIN depots depot ON d.home_depot_id = depot.depot_id
        WHERE d.license_no = :license_number
    """)
    
    result = db.execute(query, {"license_number": license_number})
    driver = result.fetchone()
    
    if not driver:
        raise HTTPException(status_code=404, detail=f"Driver with license number '{license_number}' not found")
    
    # Get assigned vehicles
    vehicle_query = text("""
        SELECT reg_code 
        FROM vehicles 
        WHERE assigned_driver_id = :driver_id
        ORDER BY reg_code
    """)
    
    vehicle_result = db.execute(vehicle_query, {"driver_id": driver.driver_id})
    assigned_vehicles = [v.reg_code for v in vehicle_result.fetchall()]
    
    return DriverSearchResult(
        name=driver.name,
        license_number=driver.license_number,
        employment_status=driver.employment_status,
        assigned_vehicles=assigned_vehicles,
        home_depot_name=driver.home_depot_name,
        created_at=driver.created_at,
        updated_at=driver.updated_at
    )

@router.get("/vehicles/by-route/{route_code}", response_model=List[VehicleSearchResult])
def get_vehicles_by_route(
    route_code: str,
    db: Session = Depends(get_db)
):
    """Get all vehicles assigned to a specific route with human-readable information."""
    
    query = text("""
        SELECT 
            v.reg_code as registration,
            v.status,
            v.capacity,
            d.name as assigned_driver_name,
            d.license_no as assigned_driver_license,
            r.short_name as assigned_route_code,
            r.long_name as assigned_route_name,
            depot.name as home_depot_name,
            v.profile_id,
            v.notes,
            v.created_at,
            v.updated_at
        FROM vehicles v
        LEFT JOIN drivers d ON v.assigned_driver_id = d.driver_id
        INNER JOIN routes r ON v.preferred_route_id = r.route_id
        LEFT JOIN depots depot ON v.home_depot_id = depot.depot_id
        WHERE LOWER(r.short_name) = LOWER(:route_code) OR LOWER(r.long_name) = LOWER(:route_code)
        ORDER BY v.reg_code
    """)
    
    result = db.execute(query, {"route_code": route_code})
    vehicles = result.fetchall()
    
    if not vehicles:
        raise HTTPException(status_code=404, detail=f"No vehicles found for route '{route_code}'")
    
    return [
        VehicleSearchResult(
            registration=v.registration,
            status=v.status,
            capacity=v.capacity,
            assigned_driver_name=v.assigned_driver_name,
            assigned_driver_license=v.assigned_driver_license,
            assigned_route_code=v.assigned_route_code,
            assigned_route_name=v.assigned_route_name,
            home_depot_name=v.home_depot_name,
            profile_id=v.profile_id,
            notes=v.notes,
            created_at=v.created_at,
            updated_at=v.updated_at
        )
        for v in vehicles
    ]