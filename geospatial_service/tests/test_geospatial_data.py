import pytest
from geospatial_service.api.geospatial_data import GeospatialData

@pytest.mark.asyncio
async def test_compute_distance_between_termini():
    """
    Test the computation of distance between route termini.
    """
    # Mock route ID and expected geometry
    mock_route_id = "test_route_1"
    mock_geometry = {
        "coordinates": [
            [40.712776, -74.005974],  # New York City
            [34.052235, -118.243683]  # Los Angeles
        ]
    }

    # Mock the get_route_geometry method
    async def mock_get_route_geometry(route_id):
        assert route_id == mock_route_id
        return mock_geometry

    GeospatialData.get_route_geometry = mock_get_route_geometry

    # Compute distance
    distance = await GeospatialData.compute_distance_between_termini(mock_route_id)

    # Assert the distance is approximately correct (within a tolerance)
    assert 3940 <= distance <= 3960, f"Unexpected distance: {distance}"