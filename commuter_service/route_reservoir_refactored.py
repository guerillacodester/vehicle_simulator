"""
Route Reservoir - Bidirectional Commuter Management

This module manages commuters spawning along route paths (not at depots).
Supports both inbound and outbound commuters at various points along routes.

Features:
- Bidirectional commuter spawning (inbound/outbound)
- Proximity-based vehicle queries
- Grid-based spatial indexing for fast lookups
- Real-time commuter management
- Socket.IO integration
"""

import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import math

from commuter_service.socketio_client import (
    SocketIOClient,
    EventTypes,
    ServiceType,
    create_route_client,
    CommuterDirection,
)
from commuter_service.location_aware_commuter import LocationAwareCommuter
from commuter_service.commuter_config import CommuterBehaviorConfig
from commuter_service.reservoir_config import ReservoirConfig
from commuter_service.base_reservoir import BaseCommuterReservoir


def get_grid_cell(
    lat: float,
    lon: float,
    cell_size: float
) -> Tuple[int, int]:
    """
    Get grid cell coordinates for spatial indexing
    
    Args:
        lat: Latitude
        lon: Longitude
        cell_size: Grid cell size in degrees
    
    Returns:
        (grid_x, grid_y) tuple
    """
    return (int(lat / cell_size), int(lon / cell_size))


def get_nearby_cells(
    lat: float,
    lon: float,
    radius_km: float,
    cell_size: float
) -> List[Tuple[int, int]]:
    """
    Get all grid cells within radius
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_km: Search radius in kilometers
        cell_size: Grid cell size in degrees
    
    Returns:
        List of (grid_x, grid_y) tuples
    """
    # Convert radius to degrees (approximate)
    radius_deg = radius_km / 111.0  # ~111km per degree latitude
    
    center_cell = get_grid_cell(lat, lon, cell_size)
    cell_radius = int(radius_deg / cell_size) + 1
    
    cells = []
    for dx in range(-cell_radius, cell_radius + 1):
        for dy in range(-cell_radius, cell_radius + 1):
            cells.append((center_cell[0] + dx, center_cell[1] + dy))
    
    return cells


@dataclass
class RouteSegment:
    """Segment of route with commuters"""
    route_id: str
    segment_id: str
    grid_cell: Tuple[int, int]
    commuters_inbound: List[LocationAwareCommuter] = field(default_factory=list)
    commuters_outbound: List[LocationAwareCommuter] = field(default_factory=list)
    total_spawned: int = 0
    total_picked_up: int = 0
    total_expired: int = 0
    
    def add_commuter(self, commuter: LocationAwareCommuter):
        """Add commuter to appropriate direction list"""
        if commuter.direction == CommuterDirection.INBOUND:
            self.commuters_inbound.append(commuter)
        else:
            self.commuters_outbound.append(commuter)
        self.total_spawned += 1
    
    def remove_commuter(self, commuter_id: str) -> Optional[LocationAwareCommuter]:
        """Remove commuter from segment"""
        # Check inbound
        for i, commuter in enumerate(self.commuters_inbound):
            if commuter.commuter_id == commuter_id:
                return self.commuters_inbound.pop(i)
        
        # Check outbound
        for i, commuter in enumerate(self.commuters_outbound):
            if commuter.commuter_id == commuter_id:
                return self.commuters_outbound.pop(i)
        
        return None
    
    def get_commuters_by_direction(
        self,
        direction: CommuterDirection
    ) -> List[LocationAwareCommuter]:
        """Get all commuters traveling in specific direction"""
        if direction == CommuterDirection.INBOUND:
            return self.commuters_inbound
        else:
            return self.commuters_outbound
    
    def count(self) -> int:
        """Total commuters in segment"""
        return len(self.commuters_inbound) + len(self.commuters_outbound)


class RouteReservoir(BaseCommuterReservoir):
    """
    Route Reservoir manages bidirectional commuters along route paths.
    
    Architecture:
    - Grid-based spatial indexing for fast proximity searches
    - Separate tracking for inbound/outbound commuters
    - Route-based organization
    - Socket.IO event integration
    - Automatic commuter expiration
    
    Usage:
        reservoir = RouteReservoir()
        await reservoir.start()
        
        # Spawn commuter along route
        commuter = await reservoir.spawn_commuter(
            route_id="ROUTE_A",
            current_location=(40.7500, -73.9950),
            destination=(40.7589, -73.9851),
            direction=CommuterDirection.OUTBOUND
        )
        
        # Vehicle queries for commuters
        commuters = reservoir.query_commuters_sync(
            route_id="ROUTE_A",
            vehicle_location=(40.7500, -73.9950),
            direction=CommuterDirection.OUTBOUND,
            max_distance=2000
        )
    """
    
    def __init__(
        self,
        socketio_url: Optional[str] = None,
        commuter_config: Optional[CommuterBehaviorConfig] = None,
        reservoir_config: Optional[ReservoirConfig] = None,
        logger: Optional[logging.Logger] = None
    ):
        super().__init__(socketio_url, commuter_config, reservoir_config, logger)
        
        # Grid-based spatial index: {grid_cell: {route_id: RouteSegment}}
        self.grid: Dict[Tuple[int, int], Dict[str, RouteSegment]] = defaultdict(dict)
        
        # Commuter to grid cell mapping for fast lookups
        self.commuter_cells: Dict[str, Tuple[int, int]] = {}
        
        # Setup Socket.IO event handlers
        self._setup_event_handlers()
    
    async def _initialize_socketio_client(self) -> SocketIOClient:
        """Initialize Socket.IO client for route reservoir"""
        return create_route_client(self.reservoir_config.socketio_url)
    
    def _setup_event_handlers(self):
        """Setup Socket.IO event handlers (deferred until client is created)"""
        pass  # Handlers will be registered after connection
    
    def _get_or_create_segment(
        self,
        route_id: str,
        grid_cell: Tuple[int, int]
    ) -> RouteSegment:
        """Get existing segment or create new one"""
        if route_id not in self.grid[grid_cell]:
            segment_id = f"{route_id}_{grid_cell[0]}_{grid_cell[1]}"
            self.grid[grid_cell][route_id] = RouteSegment(
                route_id=route_id,
                segment_id=segment_id,
                grid_cell=grid_cell
            )
            self.logger.debug(f"Created new route segment: {segment_id}")
        
        return self.grid[grid_cell][route_id]
    
    async def spawn_commuter(
        self,
        route_id: str,
        current_location: Tuple[float, float],
        destination: Tuple[float, float],
        direction: CommuterDirection = CommuterDirection.OUTBOUND,
        priority: float = 0.5
    ) -> LocationAwareCommuter:
        """
        Spawn a new commuter along route
        
        Args:
            route_id: Route identifier
            current_location: Current GPS coordinates (lat, lon)
            destination: Destination GPS coordinates (lat, lon)
            direction: Travel direction (INBOUND/OUTBOUND)
            priority: Priority level (0.0-1.0)
        
        Returns:
            LocationAwareCommuter instance
        """
        # Determine grid cell
        grid_cell = get_grid_cell(
            current_location[0],
            current_location[1],
            self.reservoir_config.grid_cell_size_degrees
        )
        
        # Get or create segment
        segment = self._get_or_create_segment(route_id, grid_cell)
        
        # Create commuter
        person_id = self._generate_commuter_id()
        commuter = LocationAwareCommuter(
            person_id=person_id,
            person_name=None,
            spawn_location=current_location,
            destination_location=destination,
            trip_purpose="commute",
            priority=priority,
            config=self.commuter_config
        )
        
        # Store additional metadata
        commuter.commuter_id = person_id
        commuter.direction = direction
        commuter.spawn_time = datetime.now()
        
        # Add to segment
        segment.add_commuter(commuter)
        self.active_commuters[commuter.commuter_id] = commuter
        self.commuter_cells[commuter.commuter_id] = grid_cell
        self.stats["total_spawned"] += 1
        
        # Calculate nearest stop (placeholder)
        nearest_stop = None
        
        # Emit spawn event
        if self.reservoir_config.enable_socketio_events and self.socketio_client:
            await self.socketio_client.emit_message(
                EventTypes.COMMUTER_SPAWNED,
                {
                    "commuter_id": commuter.commuter_id,
                    "route_id": route_id,
                    "location": {
                        "lat": current_location[0],
                        "lon": current_location[1]
                    },
                    "destination": {
                        "lat": destination[0],
                        "lon": destination[1]
                    },
                    "direction": direction.value,
                    "priority": priority,
                    "max_walking_distance": commuter.max_walking_distance_m,
                    "spawn_time": commuter.spawn_time.isoformat(),
                    "nearest_stop": nearest_stop,
                }
            )
        
        self.logger.debug(
            f"Spawned commuter {commuter.commuter_id} on route {route_id} "
            f"({direction.value})"
        )
        
        return commuter
    
    def query_commuters_sync(
        self,
        route_id: str,
        vehicle_location: Tuple[float, float],
        direction: CommuterDirection,
        max_distance: Optional[float] = None,
        max_count: Optional[int] = None
    ) -> List[LocationAwareCommuter]:
        """
        Synchronously query available commuters along route
        
        Args:
            route_id: Route identifier
            vehicle_location: Vehicle GPS coordinates (lat, lon)
            direction: Direction filter (INBOUND/OUTBOUND)
            max_distance: Maximum pickup distance in meters
            max_count: Maximum number of commuters to return
        
        Returns:
            List of available LocationAwareCommuter instances
        """
        # Use config defaults if not specified
        if max_distance is None:
            max_distance = self.reservoir_config.default_pickup_distance_meters
        if max_count is None:
            max_count = self.reservoir_config.max_commuters_per_query
        
        # Convert max_distance to km for grid search
        max_distance_km = max_distance / 1000.0
        
        # Get nearby grid cells
        nearby_cells = get_nearby_cells(
            vehicle_location[0],
            vehicle_location[1],
            max_distance_km,
            self.reservoir_config.grid_cell_size_degrees
        )
        
        available = []
        
        # Search each grid cell
        for cell in nearby_cells:
            if cell not in self.grid:
                continue
            
            if route_id not in self.grid[cell]:
                continue
            
            segment = self.grid[cell][route_id]
            commuters = segment.get_commuters_by_direction(direction)
            
            for commuter in commuters:
                distance = self.calculate_distance(
                    commuter.current_position,
                    vehicle_location
                )
                
                if distance <= max_distance:
                    available.append(commuter)
                    
                    if len(available) >= max_count:
                        return available[:max_count]
        
        return available[:max_count]
    
    def _remove_commuter_internal(self, commuter_id: str) -> bool:
        """Remove commuter from grid structures"""
        # Find commuter's grid cell
        if commuter_id not in self.commuter_cells:
            return False
        
        grid_cell = self.commuter_cells.pop(commuter_id)
        
        # Remove from all segments in that cell
        if grid_cell in self.grid:
            for segment in self.grid[grid_cell].values():
                removed = segment.remove_commuter(commuter_id)
                if removed:
                    return True
        
        return False
    
    def _find_expired_commuters(self) -> List[str]:
        """Find commuters that have waited too long"""
        expired = []
        max_wait = timedelta(minutes=self.reservoir_config.commuter_max_wait_time_minutes)
        now = datetime.now()
        
        for commuter_id, commuter in self.active_commuters.items():
            if (now - commuter.spawn_time) > max_wait:
                expired.append(commuter_id)
        
        return expired
    
    def get_stats(self) -> Dict:
        """Get route reservoir statistics"""
        base_stats = super().get_stats()
        
        # Calculate direction-specific counts
        inbound_count = sum(
            len(segment.commuters_inbound)
            for cell_segments in self.grid.values()
            for segment in cell_segments.values()
        )
        
        outbound_count = sum(
            len(segment.commuters_outbound)
            for cell_segments in self.grid.values()
            for segment in cell_segments.values()
        )
        
        # Add route-specific stats
        base_stats.update({
            "total_inbound": inbound_count,
            "total_outbound": outbound_count,
            "total_grid_cells": len(self.grid),
            "total_segments": sum(len(segments) for segments in self.grid.values()),
        })
        
        return base_stats
