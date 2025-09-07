"""
Block API Endpoints
==================
CRUD operations for Block model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from models.gtfs import Block

router = APIRouter()

@router.post("/", response_model=dict)
def create_block(
    block_data: dict,
    db: Session = Depends(get_db)
):
    """Create a new block"""
    db_block = Block(**block_data)
    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return {"message": "Block created successfully", "block_id": str(db_block.block_id)}

@router.get("/", response_model=List[dict])
def list_blocks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    country_id: Optional[UUID] = Query(None),
    route_id: Optional[UUID] = Query(None),
    service_id: Optional[UUID] = Query(None),
    db: Session = Depends(get_db)
):
    """List blocks with optional filtering"""
    query = db.query(Block)
    
    if country_id:
        query = query.filter(Block.country_id == country_id)
    if route_id:
        query = query.filter(Block.route_id == route_id)
    if service_id:
        query = query.filter(Block.service_id == service_id)
    
    blocks = query.offset(skip).limit(limit).all()
    return [
        {
            "block_id": str(b.block_id),
            "country_id": str(b.country_id),
            "route_id": str(b.route_id),
            "service_id": str(b.service_id),
            "start_time": str(b.start_time),
            "end_time": str(b.end_time)
        } for b in blocks
    ]

@router.get("/{block_id}", response_model=dict)
def get_block(
    block_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific block by ID"""
    block = db.query(Block).filter(Block.block_id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    return {
        "block_id": str(block.block_id),
        "country_id": str(block.country_id),
        "route_id": str(block.route_id),
        "service_id": str(block.service_id),
        "start_time": str(block.start_time),
        "end_time": str(block.end_time),
        "created_at": block.created_at.isoformat() if block.created_at else None
    }

@router.put("/{block_id}", response_model=dict)
def update_block(
    block_id: UUID,
    block_update: dict,
    db: Session = Depends(get_db)
):
    """Update a block"""
    block = db.query(Block).filter(Block.block_id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    for field, value in block_update.items():
        if hasattr(block, field):
            setattr(block, field, value)
    
    db.commit()
    db.refresh(block)
    return {"message": "Block updated successfully"}

@router.delete("/{block_id}")
def delete_block(
    block_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a block"""
    block = db.query(Block).filter(Block.block_id == block_id).first()
    if not block:
        raise HTTPException(status_code=404, detail="Block not found")
    
    db.delete(block)
    db.commit()
    return {"message": "Block deleted successfully"}
