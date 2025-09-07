"""
DriverAssignment API Endpoints
=============================
CRUD operations for DriverAssignment model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from models.gtfs import DriverAssignment

router = APIRouter()

@router.post("/", response_model=dict)
def create_driver_assignment(assignment_data: dict, db: Session = Depends(get_db)):
    """Create a new driver assignment"""
    db_assignment = DriverAssignment(**assignment_data)
    db.add(db_assignment)
    db.commit()
    db.refresh(db_assignment)
    return {"message": "Driver assignment created successfully", "assignment_id": str(db_assignment.assignment_id)}

@router.get("/", response_model=List[dict])
def list_driver_assignments(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    driver_id: Optional[UUID] = Query(None), block_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List driver assignments with optional filtering"""
    query = db.query(DriverAssignment)
    if driver_id: query = query.filter(DriverAssignment.driver_id == driver_id)
    if block_id: query = query.filter(DriverAssignment.block_id == block_id)
    assignments = query.offset(skip).limit(limit).all()
    return [{"assignment_id": str(a.assignment_id), "driver_id": str(a.driver_id), "block_id": str(a.block_id), "assigned_at": a.assigned_at.isoformat() if a.assigned_at else None} for a in assignments]

@router.get("/{assignment_id}", response_model=dict)
def get_driver_assignment(assignment_id: UUID, db: Session = Depends(get_db)):
    """Get a specific driver assignment by ID"""
    assignment = db.query(DriverAssignment).filter(DriverAssignment.assignment_id == assignment_id).first()
    if not assignment: raise HTTPException(status_code=404, detail="Driver assignment not found")
    return {"assignment_id": str(assignment.assignment_id), "driver_id": str(assignment.driver_id), "block_id": str(assignment.block_id), "assigned_at": assignment.assigned_at.isoformat() if assignment.assigned_at else None}

@router.delete("/{assignment_id}")
def delete_driver_assignment(assignment_id: UUID, db: Session = Depends(get_db)):
    """Delete a driver assignment"""
    assignment = db.query(DriverAssignment).filter(DriverAssignment.assignment_id == assignment_id).first()
    if not assignment: raise HTTPException(status_code=404, detail="Driver assignment not found")
    db.delete(assignment)
    db.commit()
    return {"message": "Driver assignment deleted successfully"}
