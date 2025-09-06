from uuid import uuid4
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from world.fleet_manager.models.vehicle import Vehicle
from world.fleet_manager.models.depot import Depot

# Load environment variables
load_dotenv()

# Database URL from .env file
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file")

# Initialize engine and session
engine = create_engine(DATABASE_URL, echo=False, future=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

# Step 1: Seed Vehicles (500 vehicles)
vehicles = []
for i in range(1, 501):
    vehicle = Vehicle(
        vehicle_id=uuid4(),
        reg_code=f"ZR{i:03d}",  # Vehicle registration like ZR001, ZR002, ...
        country_id=uuid4(),  # Dummy country_id for simplicity
        home_depot_id=uuid4(),  # Random depot
        preferred_route_id=uuid4(),  # Random route
        status="available",
    )
    db.add(vehicle)
    vehicles.append(vehicle)

# Commit changes to DB
db.commit()

print("[INFO] DB populated with 500 vehicles.")

# Close session
db.close()
