from sqlalchemy.orm import Session
from ..models.vehicle import Vehicle

class VehicleManager:
    def __init__(self, db: Session):
        self.db = db

    def create_vehicle(self, country_id: str, reg_code: str,
                       status: str = "available", notes: str = None) -> Vehicle:
        vehicle = Vehicle(country_id=country_id, reg_code=reg_code,
                          status=status, notes=notes)
        self.db.add(vehicle)
        self.db.commit()
        self.db.refresh(vehicle)
        return vehicle

    def get_vehicle(self, vehicle_id: str) -> Vehicle:
        return self.db.query(Vehicle).filter(Vehicle.vehicle_id == vehicle_id).first()

    def get_by_reg_code(self, reg_code: str) -> Vehicle:
        return self.db.query(Vehicle).filter(Vehicle.reg_code == reg_code).first()

    def list_vehicles(self):
        return self.db.query(Vehicle).all()

    def delete_vehicle(self, vehicle_id: str) -> bool:
        vehicle = self.get_vehicle(vehicle_id)
        if not vehicle:
            return False
        self.db.delete(vehicle)
        self.db.commit()
        return True
