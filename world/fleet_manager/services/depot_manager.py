from sqlalchemy.orm import Session
from ..models.depot import Depot


class DepotManager:
    def __init__(self, db: Session):
        self.db = db

    def create_depot(self, country_id: str, name: str,
                     location=None, capacity: int = None,
                     notes: str = None) -> Depot:
        depot = Depot(
            country_id=country_id,
            name=name,
            location=location,
            capacity=capacity,
            notes=notes
        )
        self.db.add(depot)
        self.db.commit()
        self.db.refresh(depot)
        return depot

    def get_depot(self, depot_id: str) -> Depot:
        return self.db.query(Depot).filter(Depot.depot_id == depot_id).first()

    def list_depots(self):
        return self.db.query(Depot).order_by(Depot.name).all()

    def update_depot(self, depot_id: str, **kwargs) -> Depot:
        depot = self.get_depot(depot_id)
        if not depot:
            return None
        for key, value in kwargs.items():
            setattr(depot, key, value)
        self.db.commit()
        self.db.refresh(depot)
        return depot

    def delete_depot(self, depot_id: str) -> bool:
        depot = self.get_depot(depot_id)
        if not depot:
            return False
        self.db.delete(depot)
        self.db.commit()
        return True
