from sqlalchemy import Column, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from .base import Base


class Country(Base):
    __tablename__ = "countries"

    country_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid()
    )
    iso_code = Column(Text, unique=True, nullable=False)   # e.g. "BB"
    name = Column(Text, nullable=False)                    # e.g. "Barbados"
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return f"<Country(id={self.country_id}, iso={self.iso_code}, name={self.name})>"
