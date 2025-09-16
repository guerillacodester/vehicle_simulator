"""
Route CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

try:
    from ..dependencies import get_db
except ImportError:
    from world.fleet_manager.api.start_fleet_manager import get_db
from ...models.route import Route as RouteModel
from ..schemas.route import RoutePublic, RoutePublicCreate, RoutePublicUpdate, RoutePublicWithGeometry

router = APIRouter(
    prefix="/routes",
    tags=["routes"],
    responses={404: {"description": "Not found"}},
)



@router.get("/public", response_model=List[RoutePublic])
def read_routes_public(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all routes without UUIDs for enhanced security"""
    routes = db.query(RouteModel).offset(skip).limit(limit).all()
    # Convert to public schema (excludes UUIDs)
    return [RoutePublic(
        short_name=route.short_name,
        long_name=route.long_name,
        parishes=route.parishes,
        is_active=route.is_active,
        valid_from=route.valid_from,
        valid_to=route.valid_to
    ) for route in routes]

@router.post("/public", response_model=RoutePublic)
def create_route_public(
    route: RoutePublicCreate,
    db: Session = Depends(get_db)
):
    """Create a new route with geometry using PUBLIC API with business identifiers only - NO UUIDs"""
    from ...models.country import Country as CountryModel
    from ...models.shape import Shape as ShapeModel
    from ...models.route_shape import RouteShape as RouteShapeModel
    from geoalchemy2.shape import from_shape
    from shapely.geometry import LineString
    
    # Look up country UUID from business identifier (internal use only)
    country_id = None
    if route.country_code:
        country = db.query(CountryModel).filter(CountryModel.code == route.country_code).first()
        if country:
            country_id = country.country_id
        else:
            raise HTTPException(status_code=400, detail=f"Country code '{route.country_code}' not found")
    
    # Create route with internal UUID (hidden from response)
    db_route = RouteModel(
        short_name=route.short_name,
        long_name=route.long_name,
        parishes=route.parishes,
        is_active=route.is_active,
        valid_from=route.valid_from,
        valid_to=route.valid_to,
        country_id=country_id
    )
    db.add(db_route)
    db.commit()
    db.refresh(db_route)
    
    # Handle geometry if provided
    if route.geometry and route.geometry.get('coordinates'):
        try:
            # Convert GeoJSON to Shapely LineString
            coordinates = route.geometry['coordinates']
            line = LineString(coordinates)
            
            # Create shape with geometry
            db_shape = ShapeModel(
                geom=from_shape(line, srid=4326)
            )
            db.add(db_shape)
            db.commit()
            db.refresh(db_shape)
            
            # Link route to shape
            db_route_shape = RouteShapeModel(
                route_id=db_route.route_id,
                shape_id=db_shape.shape_id,
                variant_code=route.variant_code or "default",
                is_default=True
            )
            db.add(db_route_shape)
            db.commit()
            
        except Exception as e:
            # If geometry processing fails, delete the route and raise error
            db.delete(db_route)
            db.commit()
            raise HTTPException(status_code=400, detail=f"Invalid geometry data: {str(e)}")
    
    # Return public schema (no UUIDs)
    return RoutePublic(
        short_name=db_route.short_name,
        long_name=db_route.long_name,
        parishes=db_route.parishes,
        is_active=db_route.is_active,
        valid_from=db_route.valid_from,
        valid_to=db_route.valid_to
    )

@router.get("/public/{route_code}", response_model=RoutePublic)
def read_route_public(
    route_code: str,
    db: Session = Depends(get_db)
):
    """Get a specific route by code - PUBLIC API with NO UUIDs"""
    route = db.query(RouteModel).filter(RouteModel.short_name == route_code).first()
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route {route_code} not found")
    
    return RoutePublic(
        short_name=route.short_name,
        long_name=route.long_name,
        parishes=route.parishes,
        is_active=route.is_active,
        valid_from=route.valid_from,
        valid_to=route.valid_to
    )

@router.get("/public/{route_code}/geometry", response_model=RoutePublicWithGeometry)
def read_route_with_geometry_public(
    route_code: str,
    variant: str = "default",
    db: Session = Depends(get_db)
):
    """Get a specific route with its geometry data - PUBLIC API with NO UUIDs"""
    from ...models.route_shape import RouteShape as RouteShapeModel
    from ...models.shape import Shape as ShapeModel
    from geoalchemy2.shape import to_shape
    
    # Find route
    route = db.query(RouteModel).filter(RouteModel.short_name == route_code).first()
    if route is None:
        raise HTTPException(status_code=404, detail=f"Route {route_code} not found")
    
    # Find route shape for the specified variant
    # Handle null variant codes properly - if variant is "default", look for null variant_code or is_default=True
    if variant == "default":
        route_shape = db.query(RouteShapeModel).join(ShapeModel).filter(
            RouteShapeModel.route_id == route.route_id,
            RouteShapeModel.is_default == True
        ).first()
    else:
        route_shape = db.query(RouteShapeModel).join(ShapeModel).filter(
            RouteShapeModel.route_id == route.route_id,
            RouteShapeModel.variant_code == variant
        ).first()

    geometry = None
    coordinate_count = 0

    # Debug logging
    print(f"DEBUG: Route {route_code} found, route_id: {route.route_id}")
    print(f"DEBUG: Looking for variant: {variant}")
    print(f"DEBUG: Found route_shape: {route_shape is not None}")
    if route_shape:
        print(f"DEBUG: Route shape has shape: {route_shape.shape is not None}")
        if route_shape.shape:
            print(f"DEBUG: Shape geom exists: {route_shape.shape.geom is not None}")

    if route_shape and route_shape.shape:
        try:
            # Convert PostGIS geometry to GeoJSON
            shapely_geom = to_shape(route_shape.shape.geom)
            geometry = {
                "type": "LineString",
                "coordinates": list(shapely_geom.coords)
            }
            coordinate_count = len(shapely_geom.coords)
            print(f"DEBUG: Successfully converted geometry, {coordinate_count} coordinates")
        except Exception as e:
            # If geometry conversion fails, return route without geometry
            print(f"DEBUG: Geometry conversion failed: {e}")
            pass

    return RoutePublicWithGeometry(
        short_name=route.short_name,
        long_name=route.long_name,
        parishes=route.parishes,
        is_active=route.is_active,
        valid_from=route.valid_from,
        valid_to=route.valid_to,
        geometry=geometry,
        coordinate_count=coordinate_count
    )

@router.put("/public/{route_code}", response_model=RoutePublic)
def update_route_public(
    route_code: str,
    route_update: RoutePublicUpdate,
    db: Session = Depends(get_db)
):
    """Update a route with optional geometry using PUBLIC API with business identifiers only - NO UUIDs"""
    from ...models.route_shape import RouteShape as RouteShapeModel
    from ...models.shape import Shape as ShapeModel
    from geoalchemy2.shape import from_shape
    from shapely.geometry import LineString
    
    # Find route by code
    db_route = db.query(RouteModel).filter(RouteModel.short_name == route_code).first()
    if db_route is None:
        raise HTTPException(status_code=404, detail=f"Route {route_code} not found")
    
    # Update basic fields
    if route_update.long_name is not None:
        db_route.long_name = route_update.long_name
    if route_update.parishes is not None:
        db_route.parishes = route_update.parishes
    if route_update.is_active is not None:
        db_route.is_active = route_update.is_active
    if route_update.valid_from is not None:
        db_route.valid_from = route_update.valid_from
    if route_update.valid_to is not None:
        db_route.valid_to = route_update.valid_to
    
    # Handle geometry update if provided
    if route_update.geometry and route_update.geometry.get('coordinates'):
        try:
            variant_code = route_update.variant_code or "default"
            
            # Convert GeoJSON to Shapely LineString
            coordinates = route_update.geometry['coordinates']
            line = LineString(coordinates)
            
            # Find existing route shape for this variant
            existing_route_shape = db.query(RouteShapeModel).filter(
                RouteShapeModel.route_id == db_route.route_id,
                RouteShapeModel.variant_code == variant_code
            ).first()
            
            if existing_route_shape:
                # Update existing shape geometry
                existing_route_shape.shape.geom = from_shape(line, srid=4326)
            else:
                # Create new shape and route_shape
                db_shape = ShapeModel(
                    geom=from_shape(line, srid=4326)
                )
                db.add(db_shape)
                db.commit()
                db.refresh(db_shape)
                
                db_route_shape = RouteShapeModel(
                    route_id=db_route.route_id,
                    shape_id=db_shape.shape_id,
                    variant_code=variant_code,
                    is_default=(variant_code == "default")
                )
                db.add(db_route_shape)
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid geometry data: {str(e)}")
    
    db.commit()
    db.refresh(db_route)
    
    # Return public schema (no UUIDs)
    return RoutePublic(
        short_name=db_route.short_name,
        long_name=db_route.long_name,
        parishes=db_route.parishes,
        is_active=db_route.is_active,
        valid_from=db_route.valid_from,
        valid_to=db_route.valid_to
    )

@router.delete("/public/{route_code}")
def delete_route_public(
    route_code: str,
    db: Session = Depends(get_db)
):
    """Delete a route using PUBLIC API with business identifier - NO UUIDs"""
    db_route = db.query(RouteModel).filter(RouteModel.short_name == route_code).first()
    if db_route is None:
        raise HTTPException(status_code=404, detail=f"Route {route_code} not found")
    
    db.delete(db_route)
    db.commit()
    return {"message": f"Route {route_code} deleted successfully"}


