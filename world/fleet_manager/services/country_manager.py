from sqlalchemy.orm import Session
from ..models.country import Country


class CountryManager:
    def __init__(self, db: Session):
        self.db = db

    def create_country(self, iso_code: str, name: str) -> Country:
        country = Country(iso_code=iso_code, name=name)
        self.db.add(country)
        self.db.commit()
        self.db.refresh(country)
        return country

    def get_country(self, country_id: str) -> Country:
        return (
            self.db.query(Country)
            .filter(Country.country_id == country_id)
            .first()
        )

    def get_by_iso(self, iso_code: str) -> Country:
        return (
            self.db.query(Country)
            .filter(Country.iso_code == iso_code)
            .first()
        )

    def list_countries(self):
        return self.db.query(Country).order_by(Country.name).all()

    def update_country(self, country_id: str, **kwargs) -> Country:
        country = self.get_country(country_id)
        if not country:
            return None
        for key, value in kwargs.items():
            setattr(country, key, value)
        self.db.commit()
        self.db.refresh(country)
        return country

    def delete_country(self, country_id: str) -> bool:
        country = self.get_country(country_id)
        if not country:
            return False
        self.db.delete(country)
        self.db.commit()
        return True
