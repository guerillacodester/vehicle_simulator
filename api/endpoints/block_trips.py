"""
BlockTrip API Endpoints
=======================
CRUD operations for BlockTrip model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import BlockTrip

router = APIRouter()

@router.post("/", response_model=dict)
def create_block_trip(block_trip_data: dict, db: Session = Depends(get_db)):
    """Create a new block trip"""
    db_block_trip = BlockTrip(**block_trip_data)
    db.add(db_block_trip)
    db.commit()
    return {"message": "Block trip created successfully"}

@router.get("/", response_model=List[dict])
def list_block_trips(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    block_id: Optional[UUID] = Query(None), trip_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List block trips with optional filtering"""
    query = db.query(BlockTrip)
    if block_id: query = query.filter(BlockTrip.block_id == block_id)
    if trip_id: query = query.filter(BlockTrip.trip_id == trip_id)
    block_trips = query.offset(skip).limit(limit).all()
    return [{"block_id": str(bt.block_id), "trip_id": str(bt.trip_id), "layover_minutes": bt.layover_minutes} for bt in block_trips]

@router.delete("/{block_id}/{trip_id}")
def delete_block_trip(block_id: UUID, trip_id: UUID, db: Session = Depends(get_db)):
    """Delete a block trip"""
    block_trip = db.query(BlockTrip).filter(BlockTrip.block_id == block_id, BlockTrip.trip_id == trip_id).first()
    if not block_trip: raise HTTPException(status_code=404, detail="Block trip not found")
    db.delete(block_trip)
    db.commit()
    return {"message": "Block trip deleted successfully"}
