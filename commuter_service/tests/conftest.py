"""
Pytest Configuration and Shared Fixtures
=========================================

Provides shared fixtures for all commuter service tests.
"""

import pytest
import asyncio
from typing import Dict, List
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from commuter_service.constants import (
    EARTH_RADIUS_METERS,
    MAX_BOARDING_DISTANCE_METERS,
    ROUTE_PROXIMITY_THRESHOLD_METERS,
)
from commuter_service.commuter_config import CommuterBehaviorConfig


# ============================================================================
# Event Loop Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_config() -> CommuterBehaviorConfig:
    """Provide test commuter configuration"""
    return CommuterBehaviorConfig(
        max_wait_time_minutes=30,
        patience_threshold=0.7,
        boarding_time_seconds=8,
        alighting_time_seconds=5,
        walking_speed_kmh=4.5,
        max_walking_distance_meters=500
    )


@pytest.fixture
def socketio_url() -> str:
    """Provide test Socket.IO URL"""
    return os.getenv('TEST_SOCKETIO_URL', 'http://localhost:1337')


@pytest.fixture
def strapi_url() -> str:
    """Provide test Strapi API URL"""
    return os.getenv('TEST_STRAPI_URL', 'http://localhost:1337')


# ============================================================================
# Location Fixtures
# ============================================================================

@pytest.fixture
def test_coordinates() -> Dict[str, float]:
    """Sample coordinates (Bridgetown, Barbados)"""
    return {"lat": 13.0969, "lon": -59.6145}


@pytest.fixture
def depot_location() -> Dict[str, float]:
    """Sample depot location (Speightstown Terminal)"""
    return {"lat": 13.2510, "lon": -59.6410}


@pytest.fixture
def route_point_1() -> Dict[str, float]:
    """First route point"""
    return {"lat": 13.0965, "lon": -59.6086}


@pytest.fixture
def route_point_2() -> Dict[str, float]:
    """Second route point (500m from first)"""
    return {"lat": 13.1010, "lon": -59.6120}


@pytest.fixture
def sample_route_coordinates() -> List[List[float]]:
    """Sample route with 10 points"""
    return [
        [13.0965, -59.6086],  # Point 0
        [13.0978, -59.6091],  # Point 1
        [13.0991, -59.6096],  # Point 2
        [13.1004, -59.6101],  # Point 3
        [13.1017, -59.6106],  # Point 4
        [13.1030, -59.6111],  # Point 5
        [13.1043, -59.6116],  # Point 6
        [13.1056, -59.6121],  # Point 7
        [13.1069, -59.6126],  # Point 8
        [13.1082, -59.6131],  # Point 9
    ]


# ============================================================================
# Passenger/Commuter Fixtures
# ============================================================================

@pytest.fixture
def sample_commuter_data() -> Dict:
    """Sample commuter spawn data"""
    return {
        "depot_id": "DEPOT_001",
        "destination": {"lat": 13.1082, "lon": -59.6131},
        "route_id": "ROUTE_1A",
        "trip_purpose": "work",
        "expected_wait_time": 15
    }


@pytest.fixture
def multiple_commuters_data() -> List[Dict]:
    """Multiple commuter spawn requests"""
    return [
        {
            "depot_id": "DEPOT_001",
            "destination": {"lat": 13.1082, "lon": -59.6131},
            "route_id": "ROUTE_1A",
            "trip_purpose": "work",
        },
        {
            "depot_id": "DEPOT_001",
            "destination": {"lat": 13.2510, "lon": -59.6410},
            "route_id": "ROUTE_1A",
            "trip_purpose": "shopping",
        },
        {
            "depot_id": "DEPOT_002",
            "destination": {"lat": 13.0969, "lon": -59.6145},
            "route_id": "ROUTE_2B",
            "trip_purpose": "school",
        }
    ]


# ============================================================================
# Route/Depot Fixtures
# ============================================================================

@pytest.fixture
def sample_depot_data() -> Dict:
    """Sample depot data"""
    return {
        "id": "DEPOT_001",
        "name": "Speightstown Terminal",
        "location": {"lat": 13.2510, "lon": -59.6410},
        "routes": ["ROUTE_1A", "ROUTE_2B"],
        "capacity": 50
    }


@pytest.fixture
def sample_route_data() -> Dict:
    """Sample route data"""
    return {
        "id": "ROUTE_1A",
        "code": "1A",
        "name": "Speightstown - Bridgetown",
        "coordinates": [
            [13.2510, -59.6410],
            [13.2000, -59.6300],
            [13.1500, -59.6200],
            [13.1000, -59.6100],
            [13.0969, -59.6145]
        ],
        "length_km": 22.5
    }


# ============================================================================
# Mock Objects
# ============================================================================

@pytest.fixture
def mock_socketio_client():
    """Mock Socket.IO client for testing"""
    class MockSocketIOClient:
        def __init__(self):
            self.connected = False
            self.emitted_events = []
            self.registered_handlers = {}
        
        async def connect(self):
            self.connected = True
        
        async def disconnect(self):
            self.connected = False
        
        async def emit(self, event: str, data: Dict):
            self.emitted_events.append({"event": event, "data": data})
        
        def on(self, event: str, handler):
            self.registered_handlers[event] = handler
        
        async def wait(self):
            await asyncio.sleep(0.1)
    
    return MockSocketIOClient()


@pytest.fixture
def mock_strapi_client():
    """Mock Strapi API client for testing"""
    class MockStrapiClient:
        def __init__(self):
            self.requests = []
        
        async def fetch_depots(self):
            self.requests.append("fetch_depots")
            return [
                {
                    "id": "DEPOT_001",
                    "name": "Speightstown Terminal",
                    "location": {"lat": 13.2510, "lon": -59.6410}
                }
            ]
        
        async def fetch_routes(self):
            self.requests.append("fetch_routes")
            return [
                {
                    "id": "ROUTE_1A",
                    "code": "1A",
                    "name": "Speightstown - Bridgetown"
                }
            ]
        
        async def fetch_route_coordinates(self, route_code: str):
            self.requests.append(f"fetch_route_coordinates:{route_code}")
            return [
                [13.2510, -59.6410],
                [13.1000, -59.6100],
                [13.0969, -59.6145]
            ]
    
    return MockStrapiClient()


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def mock_passenger_db():
    """Mock passenger database for testing"""
    class MockPassengerDB:
        def __init__(self):
            self.passengers = {}
            self.deleted_ids = []
        
        async def create_passenger(self, data: Dict) -> str:
            passenger_id = f"PASS_{len(self.passengers) + 1:03d}"
            self.passengers[passenger_id] = {
                **data,
                "id": passenger_id,
                "created_at": datetime.now()
            }
            return passenger_id
        
        async def get_passenger(self, passenger_id: str) -> Dict:
            return self.passengers.get(passenger_id)
        
        async def update_passenger_status(self, passenger_id: str, status: str):
            if passenger_id in self.passengers:
                self.passengers[passenger_id]["status"] = status
        
        async def delete_expired(self):
            # Mock implementation - just track that it was called
            pass
        
        async def query_nearby(self, lat: float, lon: float, radius_meters: float):
            # Simple mock - return all passengers
            return list(self.passengers.values())
    
    return MockPassengerDB()


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after each test"""
    yield
    # Cleanup code here if needed
    await asyncio.sleep(0.01)  # Small delay for async cleanup
