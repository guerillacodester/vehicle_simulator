"""
Block CRUD router for Fleet Management API
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from ..dependencies import get_db
from ...models.block import Block as BlockModel
from ..schemas.block import Block, BlockCreate, BlockUpdate

router = APIRouter(
    prefix="/blocks",
    tags=["blocks"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=Block)
def create_block(
    block: BlockCreate,
    db: Session = Depends(get_db)
):
    """Create a new block"""
    db_block = BlockModel(**block.dict())
    db.add(db_block)
    db.commit()
    db.refresh(db_block)
    return db_block

@router.get("/", response_model=List[Block])
def read_blocks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all blocks with pagination"""
    blocks = db.query(BlockModel).offset(skip).limit(limit).all()
    return blocks

@router.get("/{block_id}", response_model=Block)
def read_block(
    block_id: UUID,
    db: Session = Depends(get_db)
):
    """Get a specific block by ID"""
    block = db.query(BlockModel).filter(BlockModel.block_id == block_id).first()
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    return block

@router.get("/service/{service_id}", response_model=List[Block])
def read_blocks_by_service(
    service_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all blocks for a specific service"""
    blocks = db.query(BlockModel).filter(BlockModel.service_id == service_id).all()
    return blocks

@router.put("/{block_id}", response_model=Block)
def update_block(
    block_id: UUID,
    block: BlockUpdate,
    db: Session = Depends(get_db)
):
    """Update a specific block"""
    db_block = db.query(BlockModel).filter(BlockModel.block_id == block_id).first()
    if db_block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    
    update_data = block.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_block, field, value)
    
    db.commit()
    db.refresh(db_block)
    return db_block

@router.delete("/{block_id}")
def delete_block(
    block_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a specific block"""
    block = db.query(BlockModel).filter(BlockModel.block_id == block_id).first()
    if block is None:
        raise HTTPException(status_code=404, detail="Block not found")
    
    db.delete(block)
    db.commit()
    return {"message": "Block deleted successfully"}
