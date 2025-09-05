# world/fleet_manager/models/vehicle.py
from sqlalchemy import (
    Column,
    Text,
    DateTime,
    ForeignKey,
    func,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from .base import Base   # ✅ import the single shared Base

class Vehicle(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )

    country_id = Column(
        UUID(as_uuid=True),
        ForeignKey("countries.country_id"),
        nullable=False,
    )

    # ✅ enforce uniqueness + regex pattern
    reg_code = Column(Text, nullable=False, unique=True)

    home_depot_id = Column(UUID(as_uuid=True), ForeignKey("depots.depot_id"))
    preferred_route_id = Column(UUID(as_uuid=True), ForeignKey("routes.route_id"))

    status = Column(
        ENUM(
            "available",
            "active",
            "inactive",
            "maintenance",
            name="vehicle_status",
            create_type=False,
        ),
        nullable=False,
        server_default="available",
    )

    profile_id = Column(Text)
    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        onupdate=func.now(),
    )

    __table_args__ = (
        # ✅ Only allow ZR + 2 or 3 digits (ZR12 or ZR123)
        CheckConstraint(
            "reg_code ~ '^ZR[0-9]{2,3}$'",
            name="vehicles_reg_code_format_chk",
        ),
        UniqueConstraint("reg_code", name="vehicles_reg_code_key"),
    )
