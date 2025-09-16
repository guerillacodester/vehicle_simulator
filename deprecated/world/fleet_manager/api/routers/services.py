"""
Service CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.service import Service as ServiceModel
from ..schemas.service import Service, ServiceCreate, ServiceUpdate

router = APIRouter(
    prefix="/services",
    tags=["services"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Service)
def create_service(
    service: ServiceCreate,
    db: Session = Depends(get_db)
):
    """Create a new service"""
    db_service = ServiceModel(**service.dict())
    db.add(db_service)
    db.commit()
    db.refresh(db_service)
    return db_service

@router.get("/", response_model=List[Service])
def read_services(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all services with pagination"""
    services = db.query(ServiceModel).offset(skip).limit(limit).all()
    return services

@router.get("/{service_id}", response_model=Service)
def read_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific service by ID"""
    service = db.query(ServiceModel).filter(ServiceModel.service_id == service_id).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    return service

@router.put("/{service_id}", response_model=Service)
def update_service(
    service_id: UUID,
    service: ServiceUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific service"""
    db_service = db.query(ServiceModel).filter(ServiceModel.service_id == service_id).first()
    if db_service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    
    update_data = service.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_service, field, value)
    
    db.commit()
    db.refresh(db_service)
    return db_service

@router.delete("/{service_id}")
def delete_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific service"""
    service = db.query(ServiceModel).filter(ServiceModel.service_id == service_id).first()
    if service is None:
        raise HTTPException(status_code=404, detail="Service not found")
    
    db.delete(service)
    db.commit()
    return {"message": "Service deleted successfully"}
