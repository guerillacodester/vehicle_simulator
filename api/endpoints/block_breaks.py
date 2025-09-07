"""
BlockBreak API Endpoints
========================
CRUD operations for BlockBreak model
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from ..database import get_db
from ...models.gtfs import BlockBreak

router = APIRouter()

@router.post("/", response_model=dict)
def create_block_break(block_break_data: dict, db: Session = Depends(get_db)):
    """Create a new block break"""
    db_block_break = BlockBreak(**block_break_data)
    db.add(db_block_break)
    db.commit()
    db.refresh(db_block_break)
    return {"message": "Block break created successfully", "break_id": str(db_block_break.break_id)}

@router.get("/", response_model=List[dict])
def list_block_breaks(
    skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000),
    block_id: Optional[UUID] = Query(None), db: Session = Depends(get_db)
):
    """List block breaks with optional filtering"""
    query = db.query(BlockBreak)
    if block_id: query = query.filter(BlockBreak.block_id == block_id)
    block_breaks = query.offset(skip).limit(limit).all()
    return [{"break_id": str(bb.break_id), "block_id": str(bb.block_id), "break_start": str(bb.break_start), "break_end": str(bb.break_end), "break_duration": bb.break_duration} for bb in block_breaks]

@router.delete("/{break_id}")
def delete_block_break(break_id: UUID, db: Session = Depends(get_db)):
    """Delete a block break"""
    block_break = db.query(BlockBreak).filter(BlockBreak.break_id == break_id).first()
    if not block_break: raise HTTPException(status_code=404, detail="Block break not found")
    db.delete(block_break)
    db.commit()
    return {"message": "Block break deleted successfully"}
