"""
Service API Endpoints
====================
CRUD operations for Service model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from models.gtfs import Service

router = APIRouter()

@router.post("/", response_model=dict)
def create_service(
    service_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new service"""
    db_service = Service(**service_data)
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return {"message": "Service created successfully", "service_id": str(db_service.service_id)}

@router.get("/", response_model=List[dict])
def list_services(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List services with optional filtering"""
    query = db.query(Service)
    
    if country_id:
        query = query.filter(Service.country_id == country_id)
    
    services = query.offset(skip).limit(limit).all()
    return [{"service_id": str(s.service_id), "name": s.name, "country_id": str(s.country_id)} for s in services]

@router.get("/{service_id}", response_model=dict)
def get_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific service by ID"""
    service = db.query(Service).filter(Service.service_id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return {
        "service_id": str(service.service_id),
        "name": service.name,
        "country_id": str(service.country_id),
        "schedule": {
            "mon": service.mon,
            "tue": service.tue,
            "wed": service.wed,
            "thu": service.thu,
            "fri": service.fri,
            "sat": service.sat,
            "sun": service.sun
        }
    }

@router.delete("/{service_id}")
def delete_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a service"""
    service = db.query(Service).filter(Service.service_id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    db.delete(service)
    db.commit()
    return {"message": "Service deleted successfully"}
