# world/fleet_manager/services/vehicle_manager.py
from sqlalchemy.orm import Session
from uuid import UUID
from ..models.vehicle import Vehicle

class VehicleManager:
    def __init__(self, db: Session):
        self.db = db

    def create_vehicle(
        self,
        country_id: UUID,
        reg_code: str,
        status: str = "available",
        notes: str | None = None,
        home_depot_id: UUID | None = None,
        preferred_route_id: UUID | None = None,
        profile_id: str | None = None,
    ) -> Vehicle:
        vehicle = Vehicle(
            country_id=country_id,
            reg_code=reg_code,
            status=status,
            notes=notes,
            home_depot_id=home_depot_id,
            preferred_route_id=preferred_route_id,
            profile_id=profile_id,
        )
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def get_vehicle(self, vehicle_id: UUID) -> Vehicle | None:
        return self.db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()

    def get_by_reg_code(self, reg_code: str) -> Vehicle | None:
        return self.db.query(Vehicle).filter(Vehicle.reg_code == reg_code).first()

    def list_vehicles(self) -> list[Vehicle]:
        return self.db.query(Vehicle).all()

    def update_vehicle(self, vehicle_id: UUID, **kwargs) -> Vehicle | None:
        v = self.get_vehicle(vehicle_id)
        if not v:
            return None
        for key, val in kwargs.items():
            setattr(v, key, val)
        self.db.commit()
        self.db.refresh(v)
        return v

    def delete_vehicle(self, vehicle_id: UUID) -> bool:
        v = self.get_vehicle(vehicle_id)
        if not v:
            return False
        self.db.delete(v)
        self.db.commit()
        return True
