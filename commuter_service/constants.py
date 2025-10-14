"""
Constants and Configuration Values
===================================

Central location for all magic numbers and configuration constants
used throughout the commuter service.

This improves maintainability and makes it easy to tune system behavior.
"""

# Geographic Constants
EARTH_RADIUS_METERS = 6371000  # Earth's radius in meters
EARTH_RADIUS_KM = 6371.0  # Earth's radius in kilometers

# Spatial Grid Configuration
GRID_CELL_SIZE_DEGREES = 0.01  # ~1km at equator
GRID_CELL_SIZE_KM = 1.0  # Approximate grid cell size

# Distance Thresholds (meters)
DEFAULT_SEARCH_RADIUS_METERS = 100  # Default passenger search radius
MAX_BOARDING_DISTANCE_METERS = 50  # Maximum distance for boarding
DEPOT_PROXIMITY_THRESHOLD_METERS = 200  # Distance to consider "at depot"
ROUTE_PROXIMITY_THRESHOLD_METERS = 100  # Distance to route for spawning
MAX_WALKING_DISTANCE_METERS = 1000  # Maximum walking distance for passengers

# Distance Thresholds (kilometers)
DEFAULT_SEARCH_RADIUS_KM = 1.0
NEARBY_CELL_SEARCH_RADIUS_KM = 2.0

# Time Constants (minutes)
DEFAULT_WAIT_TIME_MINUTES = 30  # Default max wait time before expiration
MIN_SPAWN_INTERVAL_MINUTES = 1  # Minimum time between spawns
MAX_JOURNEY_TIME_MINUTES = 120  # Maximum expected journey time

# Time Constants (seconds)
EXPIRATION_CHECK_INTERVAL_SECONDS = 10  # How often to check for expired passengers
SPAWN_CHECK_INTERVAL_SECONDS = 60  # How often to check for new spawns
POSITION_UPDATE_INTERVAL_SECONDS = 5  # Vehicle position update frequency

# Capacity and Limits
DEFAULT_VEHICLE_CAPACITY = 30  # Default seats per vehicle
MAX_QUERY_RESULTS = 50  # Maximum passengers returned in a query
MAX_PRIORITY = 1.0  # Maximum priority value
MIN_PRIORITY = 0.0  # Minimum priority value

# Socket.IO Configuration
SOCKETIO_RECONNECT_DELAY_SECONDS = 5  # Delay between reconnection attempts
SOCKETIO_MAX_RECONNECT_ATTEMPTS = 10  # Maximum reconnection attempts

# Database Configuration
DB_QUERY_TIMEOUT_SECONDS = 30  # Maximum time for database query
DB_CONNECTION_POOL_SIZE = 10  # Number of database connections

# API Configuration
API_REQUEST_TIMEOUT_SECONDS = 30  # Maximum time for API request
API_RETRY_ATTEMPTS = 3  # Number of retry attempts for failed requests
API_RETRY_DELAY_SECONDS = 2  # Delay between retry attempts

# Logging Configuration
LOG_STATS_INTERVAL_SECONDS = 300  # How often to log statistics (5 minutes)

# Spawning Configuration
BASE_SPAWN_RATE_MULTIPLIER = 1.0  # Base multiplier for spawn rates
MIN_SPAWN_RATE = 0.01  # Minimum spawns per minute
MAX_SPAWN_RATE = 10.0  # Maximum spawns per minute

# Precision and Rounding
COORDINATE_PRECISION_DIGITS = 6  # Decimal places for lat/lon
DISTANCE_PRECISION_DIGITS = 2  # Decimal places for distances
PRIORITY_PRECISION_DIGITS = 3  # Decimal places for priority values
