from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from .. import deps
from ..schemas.timetable import TimetableCreate, TimetableRead, TimetableUpdate
from ...services.timetable_manager import TimetableManager

router = APIRouter(prefix="/api/v1/timetables", tags=["timetables"])

@router.get("/", response_model=list[TimetableRead])
def list_all(manager: TimetableManager = Depends(deps.get_timetable_manager)):
    return manager.list_all()

@router.get("/today", response_model=list[TimetableRead])
def list_today(manager: TimetableManager = Depends(deps.get_timetable_manager)):
    return manager.list_for_today()

@router.get("/by-vehicle/{vehicle_id}", response_model=list[TimetableRead])
def list_for_vehicle(vehicle_id: UUID, manager: TimetableManager = Depends(deps.get_timetable_manager)):
    return manager.list_for_vehicle(vehicle_id)

@router.post("/", response_model=TimetableRead, status_code=201)
def create_timetable(payload: TimetableCreate, manager: TimetableManager = Depends(deps.get_timetable_manager)):
    return manager.create_timetable(**payload.dict())

@router.delete("/{timetable_id}", status_code=204)
def delete_timetable(timetable_id: UUID, manager: TimetableManager = Depends(deps.get_timetable_manager)):
    ok = manager.delete_timetable(timetable_id)
    if not ok:
        raise HTTPException(404, detail="Timetable not found")
    return
