from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime, date
from ..models.timetable import Timetable

class TimetableManager:
    def __init__(self, db: Session):
        self.db = db

    def list_all(self):
        return self.db.query(Timetable).order_by(Timetable.departure_time).all()

    def get_by_id(self, timetable_id: UUID):
        return self.db.query(Timetable).filter_by(timetable_id=timetable_id).first()

    def list_for_vehicle(self, vehicle_id: UUID):
        return self.db.query(Timetable).filter_by(vehicle_id=vehicle_id).order_by(Timetable.departure_time).all()

    def list_for_today(self):
        today = date.today()
        return (
            self.db.query(Timetable)
            .filter(
                Timetable.departure_time >= datetime.combine(today, datetime.min.time()),
                Timetable.departure_time <= datetime.combine(today, datetime.max.time()),
            )
            .order_by(Timetable.departure_time)
            .all()
        )

    def create_timetable(self, **kwargs) -> Timetable:
        item = Timetable(**kwargs)
        self.db.add(item)
        self.db.commit()
        self.db.refresh(item)
        return item

    def delete_timetable(self, timetable_id: UUID) -> bool:
        item = self.get_by_id(timetable_id)
        if not item:
            return False
        self.db.delete(item)
        self.db.commit()
        return True
