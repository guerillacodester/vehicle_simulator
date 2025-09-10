"""
Shape CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
from shapely.geometry import shape as shapely_shape
from geoalchemy2 import WKTElement

try:
    from ..dependencies import get_db
except ImportError:
    from world.fleet_manager.api.start_fleet_manager import get_db
from ...models.shape import Shape as ShapeModel
from ..schemas.shape import Shape, ShapeCreate

router = APIRouter(
    prefix="/shapes",
    tags=["shapes"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Shape)
def create_shape(
    shape: ShapeCreate,
    db: Session = Depends(get_db)
):
    """Create a new shape"""
    from sqlalchemy import func
    import json
    
    # Convert GeoJSON to WKT
    geom_obj = shape.geom
    shapely_geom = shapely_shape(geom_obj)
    wkt = shapely_geom.wkt
    wkt_element = WKTElement(wkt, srid=4326)
    
    db_shape = ShapeModel(geom=wkt_element)
    db.add(db_shape)
    db.commit()
    db.refresh(db_shape)
    
    # Return the shape with GeoJSON geometry
    return {
        "shape_id": db_shape.shape_id,
        "geom": shape.geom  # Return the original GeoJSON
    }

@router.get("/", response_model=List[Shape])
def read_shapes(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all shapes with pagination"""
    from sqlalchemy import func
    import json
    
    # Get shapes with geometry as GeoJSON
    shapes = db.query(
        ShapeModel.shape_id,
        func.ST_AsGeoJSON(ShapeModel.geom).label('geom_geojson')
    ).offset(skip).limit(limit).all()
    
    # Convert to response format
    result = []
    for shape in shapes:
        geom_dict = json.loads(shape.geom_geojson) if shape.geom_geojson else None
        result.append({
            "shape_id": shape.shape_id,
            "geom": geom_dict
        })
    
    return result

@router.get("/{shape_id}", response_model=Shape)
def read_shape(
    shape_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific shape by ID"""
    from sqlalchemy import func
    from shapely.wkb import loads as wkb_loads
    from shapely.geometry import mapping
    
    # Get shape with geometry as GeoJSON
    shape = db.query(
        ShapeModel.shape_id,
        func.ST_AsGeoJSON(ShapeModel.geom).label('geom_geojson')
    ).filter(ShapeModel.shape_id == shape_id).first()
    
    if shape is None:
        raise HTTPException(status_code=404, detail="Shape not found")
    
    # Parse the GeoJSON string to dict
    import json
    geom_dict = json.loads(shape.geom_geojson) if shape.geom_geojson else None
    
    return {
        "shape_id": shape.shape_id,
        "geom": geom_dict
    }
