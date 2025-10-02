"""
Commuter Reservoir System
=========================

Implements reservoir-based commuter spawning where commuters accumulate in 
location-based pools and are consumed by depot managers/conductors when needed.

Key Features:
- GTFS-compliant route geometry integration
- Statistical realism with Poisson distribution
- Time/location-based spawning
- Efficient spatial queries for commuter pickup
- Realistic waiting time modeling
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import math
import random
import numpy as np

from .simple_commuter import SimpleCommuter
from .strapi_api_client import StrapiApiClient, DepotData, RouteData


@dataclass(frozen=True)
class CommuterReservation:
    """A commuter waiting in the reservoir with spatial/temporal constraints"""
    commuter: SimpleCommuter
    spawn_time: datetime
    spawn_location: tuple  # (lat, lon) - using tuple for immutability
    route_id: str
    depot_id: str
    trip_purpose: str
    priority: float
    max_wait_minutes: int = 30
    
    @property
    def is_expired(self) -> bool:
        """Check if commuter reservation has expired"""
        return (datetime.now() - self.spawn_time).total_seconds() > (self.max_wait_minutes * 60)
    
    @property
    def wait_time_minutes(self) -> float:
        """Current wait time in minutes"""
        return (datetime.now() - self.spawn_time).total_seconds() / 60


@dataclass
class ReservoirQuery:
    """Query parameters for retrieving commuters from reservoir"""
    depot_id: Optional[str] = None
    route_id: Optional[str] = None
    location: Optional[tuple] = None  # (lat, lon)
    radius_km: float = 1.0
    max_commuters: int = 50
    max_wait_minutes: Optional[int] = None
    trip_purposes: Optional[List[str]] = None


class CommuterReservoir:
    """
    Central reservoir for storing spawned commuters with spatial/temporal indexing.
    
    Commuters accumulate here and can be queried by location, route, depot, etc.
    Implements realistic statistical spawning based on GTFS route geometry.
    """
    
    def __init__(self, api_client: StrapiApiClient):
        self.api_client = api_client
        
        # Reservoir storage - indexed for efficient queries
        self.commuters: List[CommuterReservation] = []
        self.depot_index: Dict[str, List[CommuterReservation]] = defaultdict(list)
        self.route_index: Dict[str, List[CommuterReservation]] = defaultdict(list)
        
        # Spatial grid for location-based queries (simplified spatial index)
        self.spatial_grid: Dict[Tuple[int, int], List[CommuterReservation]] = defaultdict(list)
        self.grid_resolution = 0.01  # ~1km grid cells
        
        # Statistics and monitoring
        self.total_spawned = 0
        self.total_consumed = 0
        self.spawn_history: List[Dict[str, Any]] = []
        
        # Route geometry cache for spawning locations
        self.route_geometries: Dict[str, List[List[float]]] = {}
        self.depot_locations: Dict[str, Dict[str, float]] = {}
    
    async def initialize(self) -> bool:
        """Initialize reservoir with route and depot data"""
        try:
            logging.info("🏊 Initializing Commuter Reservoir...")
            
            # Cache depot locations
            depots = await self.api_client.get_all_depots()
            for depot in depots:
                if depot.location:
                    self.depot_locations[depot.depot_id] = depot.location
            
            # Cache route geometries  
            routes = await self.api_client.get_all_routes()
            for route in routes:
                if route.geometry_coordinates:
                    self.route_geometries[route.short_name] = route.geometry_coordinates
            
            logging.info(f"✅ Reservoir initialized: {len(self.depot_locations)} depots, "
                        f"{len(self.route_geometries)} routes with geometry")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to initialize reservoir: {e}")
            return False
    
    async def spawn_commuters_statistical(self, current_time: datetime, 
                                         time_window_minutes: int = 5) -> int:
        """
        Spawn commuters using statistical models based on GTFS geometry and real-world patterns.
        
        Returns number of commuters spawned in this cycle.
        """
        spawned_count = 0
        
        try:
            # Calculate time-based spawn rate modifier
            time_factor = self._get_time_based_factor(current_time)
            
            # Spawn commuters for each depot-route combination
            for depot_id, depot_location in self.depot_locations.items():
                for route_id, route_geometry in self.route_geometries.items():
                    
                    # Calculate spawn demand for this depot-route pair
                    spawn_rate = self._calculate_spawn_rate(
                        depot_id, route_id, current_time, time_factor
                    )
                    
                    # Use Poisson distribution for realistic commuter arrivals
                    expected_commuters = spawn_rate * (time_window_minutes / 60.0)
                    commuter_count = max(0, int(np.random.poisson(expected_commuters)))
                    
                    # Spawn commuters along route geometry
                    for _ in range(commuter_count):
                        commuter_reservation = await self._create_commuter_reservation(
                            depot_id, route_id, route_geometry, current_time
                        )
                        
                        if commuter_reservation:
                            self._add_to_reservoir(commuter_reservation)
                            spawned_count += 1
            
            # Clean up expired reservations
            self._cleanup_expired_reservations()
            
            # Update statistics
            self.total_spawned += spawned_count
            self.spawn_history.append({
                'timestamp': current_time,
                'spawned': spawned_count,
                'total_in_reservoir': len(self.commuters),
                'time_factor': time_factor
            })
            
            logging.debug(f"🎯 Spawned {spawned_count} commuters (reservoir: {len(self.commuters)})")
            
        except Exception as e:
            logging.error(f"❌ Error spawning commuters: {e}")
        
        return spawned_count
    
    def query_commuters(self, query: ReservoirQuery) -> List[SimpleCommuter]:
        """
        Query commuters from reservoir based on spatial/temporal/route criteria.
        
        This is called by depot managers/conductors to get commuters for pickup.
        """
        matching_commuters = []
        
        try:
            candidates = self._get_query_candidates(query)
            
            for reservation in candidates:
                # Skip expired commuters
                if reservation.is_expired:
                    continue
                
                # Apply spatial filter if location specified
                if query.location and query.radius_km:
                    distance = self._calculate_distance(
                        query.location, reservation.spawn_location
                    )
                    if distance > query.radius_km:
                        continue
                
                # Apply wait time filter
                if query.max_wait_minutes and reservation.wait_time_minutes > query.max_wait_minutes:
                    continue
                
                # Apply trip purpose filter
                if query.trip_purposes and reservation.trip_purpose not in query.trip_purposes:
                    continue
                
                matching_commuters.append(reservation.commuter)
                
                # Stop when we have enough commuters
                if len(matching_commuters) >= query.max_commuters:
                    break
            
            logging.debug(f"🔍 Query found {len(matching_commuters)} commuters "
                         f"(from {len(candidates)} candidates)")
            
        except Exception as e:
            logging.error(f"❌ Error querying commuters: {e}")
        
        return matching_commuters
    
    def consume_commuters(self, commuters: List[SimpleCommuter]) -> int:
        """
        Remove commuters from reservoir (called when picked up by vehicles).
        
        Returns number of commuters successfully removed.
        """
        consumed_count = 0
        commuter_ids = {c.person_id for c in commuters}
        
        try:
            # Remove from main list and indices
            remaining_commuters = []
            
            for reservation in self.commuters:
                if reservation.commuter.person_id in commuter_ids:
                    # Remove from indices
                    self._remove_from_indices(reservation)
                    consumed_count += 1
                else:
                    remaining_commuters.append(reservation)
            
            self.commuters = remaining_commuters
            self.total_consumed += consumed_count
            
            logging.debug(f"🚌 Consumed {consumed_count} commuters from reservoir")
            
        except Exception as e:
            logging.error(f"❌ Error consuming commuters: {e}")
        
        return consumed_count
    
    def get_reservoir_status(self) -> Dict[str, Any]:
        """Get current reservoir status and statistics"""
        depot_counts = {depot_id: len(reservations) 
                       for depot_id, reservations in self.depot_index.items()}
        
        route_counts = {route_id: len(reservations)
                       for route_id, reservations in self.route_index.items()}
        
        # Also include loaded depot/route data for debugging
        if not depot_counts:
            depot_counts = {depot_id: 0 for depot_id in self.depot_locations.keys()}
        if not route_counts:
            route_counts = {route_id: 0 for route_id in self.route_geometries.keys()}
        
        # Average wait times
        current_wait_times = [r.wait_time_minutes for r in self.commuters]
        avg_wait_time = sum(current_wait_times) / len(current_wait_times) if current_wait_times else 0
        
        return {
            'total_commuters': len(self.commuters),
            'total_spawned': self.total_spawned,
            'total_consumed': self.total_consumed,
            'efficiency_rate': (self.total_consumed / max(1, self.total_spawned)) * 100,
            'average_wait_minutes': round(avg_wait_time, 1),
            'commuters_by_depot': depot_counts,
            'commuters_by_route': route_counts,
            'spatial_grid_cells': len(self.spatial_grid),
            'recent_spawn_rate': self._calculate_recent_spawn_rate()
        }
    
    # --- Private Methods ---
    
    def _get_time_based_factor(self, current_time: datetime) -> float:
        """Calculate time-based spawn rate modifier (peak/off-peak/night)"""
        hour = current_time.hour
        
        # Peak hours: 7-9am and 5-7pm
        if 7 <= hour <= 9 or 17 <= hour <= 19:
            return 2.5  # Peak multiplier
        # Business hours: 9am-5pm
        elif 9 <= hour <= 17:
            return 1.2  # Moderate activity
        # Evening: 7pm-10pm
        elif 19 <= hour <= 22:
            return 0.8  # Social/recreation
        # Night: 10pm-6am
        else:
            return 0.2  # Minimal activity
    
    def _calculate_spawn_rate(self, depot_id: str, route_id: str, 
                            current_time: datetime, time_factor: float) -> float:
        """Calculate commuters per hour for depot-route combination"""
        # Base rate (commuters per hour)
        base_rate = 5.0
        
        # Route complexity factor (longer routes = more commuters)
        route_geometry = self.route_geometries.get(route_id, [])
        route_factor = min(2.0, len(route_geometry) / 100.0) if route_geometry else 1.0
        
        # Depot capacity factor (assumed from depot naming/type)
        depot_factor = 1.5 if 'MAIN' in depot_id.upper() else 1.0
        
        # Day of week factor
        weekday_factor = 1.0 if current_time.weekday() < 5 else 0.6  # Less on weekends
        
        final_rate = base_rate * time_factor * route_factor * depot_factor * weekday_factor
        return max(0.1, final_rate)  # Minimum rate
    
    async def _create_commuter_reservation(self, depot_id: str, route_id: str,
                                          route_geometry: List[List[float]], 
                                          current_time: datetime) -> Optional[CommuterReservation]:
        """Create a commuter reservation with realistic attributes"""
        try:
            # Select spawn location along route (weighted toward depot)
            spawn_location = self._select_spawn_location(depot_id, route_geometry)
            if not spawn_location:
                return None
            
            # Generate commuter
            commuter_id = f"CMT_{depot_id}_{route_id}_{int(current_time.timestamp())}_{random.randint(1000, 9999)}"
            
            trip_purpose = self._determine_trip_purpose(current_time)
            priority = self._calculate_priority(trip_purpose, current_time)
            
            # Create SimpleCommuter
            commuter = SimpleCommuter(
                person_id=commuter_id,
                person_type="Commuter",
                person_name=f"Commuter_{trip_purpose}",
                origin_stop_id=depot_id,
                destination_stop_id=route_id,
                depart_time=current_time,
                trip_purpose=trip_purpose,
                priority=priority,
                spawn_location=spawn_location
            )
            
            # Create reservation
            reservation = CommuterReservation(
                commuter=commuter,
                spawn_time=current_time,
                spawn_location=spawn_location,
                route_id=route_id,
                depot_id=depot_id,
                trip_purpose=trip_purpose,
                priority=priority,
                max_wait_minutes=self._calculate_max_wait(trip_purpose)
            )
            
            return reservation
            
        except Exception as e:
            logging.error(f"❌ Error creating commuter reservation: {e}")
            return None
    
    def _select_spawn_location(self, depot_id: str, route_geometry: List[List[float]]) -> Optional[tuple]:
        """Select realistic spawn location (depot or along route)"""
        if not route_geometry:
            # Fallback to depot location
            depot_loc = self.depot_locations.get(depot_id)
            return (depot_loc['lat'], depot_loc['lon']) if depot_loc else None
        
        # 70% chance spawn at depot, 30% along route
        if random.random() < 0.7:
            depot_loc = self.depot_locations.get(depot_id)
            return (depot_loc['lat'], depot_loc['lon']) if depot_loc else None
        else:
            # Random point along route
            point_index = random.randint(0, len(route_geometry) - 1)
            lon, lat = route_geometry[point_index]
            return (lat, lon)
    
    def _determine_trip_purpose(self, current_time: datetime) -> str:
        """Determine trip purpose based on time patterns"""
        hour = current_time.hour
        
        if 6 <= hour <= 10 or 16 <= hour <= 19:
            return random.choice(['work', 'work', 'education', 'medical'])
        elif 10 <= hour <= 16:
            return random.choice(['shopping', 'medical', 'personal', 'recreation'])
        elif 19 <= hour <= 23:
            return random.choice(['social', 'recreation', 'shopping'])
        else:
            return random.choice(['medical', 'personal', 'work'])
    
    def _calculate_priority(self, trip_purpose: str, current_time: datetime) -> float:
        """Calculate commuter priority (0.0-1.0)"""
        purpose_priorities = {
            'work': 0.9,
            'medical': 1.0,
            'education': 0.8,
            'shopping': 0.4,
            'social': 0.3,
            'recreation': 0.2,
            'personal': 0.6
        }
        
        base_priority = purpose_priorities.get(trip_purpose, 0.5)
        
        # Time urgency factor
        hour = current_time.hour
        if 7 <= hour <= 9 or 17 <= hour <= 19:  # Rush hours
            base_priority += 0.1
        
        return min(1.0, base_priority)
    
    def _calculate_max_wait(self, trip_purpose: str) -> int:
        """Calculate maximum wait time based on trip purpose"""
        wait_times = {
            'work': 20,      # Work trips - less tolerance for waiting
            'medical': 15,   # Medical - urgent
            'education': 25, # School - somewhat flexible
            'shopping': 45,  # Shopping - more flexible
            'social': 60,    # Social - very flexible
            'recreation': 60, # Recreation - very flexible
            'personal': 30   # Personal errands - moderate
        }
        
        return wait_times.get(trip_purpose, 30)
    
    def _add_to_reservoir(self, reservation: CommuterReservation):
        """Add commuter reservation to reservoir with indexing"""
        self.commuters.append(reservation)
        
        # Add to depot index
        self.depot_index[reservation.depot_id].append(reservation)
        
        # Add to route index
        self.route_index[reservation.route_id].append(reservation)
        
        # Add to spatial grid
        grid_key = self._get_grid_key(reservation.spawn_location)
        self.spatial_grid[grid_key].append(reservation)
    
    def _remove_from_indices(self, reservation: CommuterReservation):
        """Remove commuter reservation from all indices"""
        # Remove from depot index
        if reservation.depot_id in self.depot_index:
            try:
                self.depot_index[reservation.depot_id].remove(reservation)
            except ValueError:
                pass
        
        # Remove from route index
        if reservation.route_id in self.route_index:
            try:
                self.route_index[reservation.route_id].remove(reservation)
            except ValueError:
                pass
        
        # Remove from spatial grid
        grid_key = self._get_grid_key(reservation.spawn_location)
        if grid_key in self.spatial_grid:
            try:
                self.spatial_grid[grid_key].remove(reservation)
            except ValueError:
                pass
    
    def _get_grid_key(self, location: tuple) -> Tuple[int, int]:
        """Get spatial grid key for location"""
        lat, lon = location
        lat_key = int(lat / self.grid_resolution)
        lon_key = int(lon / self.grid_resolution)
        return (lat_key, lon_key)
    
    def _get_query_candidates(self, query: ReservoirQuery) -> List[CommuterReservation]:
        """Get candidate commuters for query (uses indices for efficiency)"""
        candidates = set()
        
        # Use depot index if specified
        if query.depot_id:
            candidates.update(self.depot_index.get(query.depot_id, []))
        
        # Use route index if specified
        if query.route_id:
            route_candidates = set(self.route_index.get(query.route_id, []))
            if candidates:
                candidates = candidates.intersection(route_candidates)
            else:
                candidates = route_candidates
        
        # Use spatial index if location specified
        if query.location:
            spatial_candidates = set()
            center_key = self._get_grid_key(query.location)
            
            # Check surrounding grid cells
            for lat_offset in [-1, 0, 1]:
                for lon_offset in [-1, 0, 1]:
                    grid_key = (center_key[0] + lat_offset, center_key[1] + lon_offset)
                    spatial_candidates.update(self.spatial_grid.get(grid_key, []))
            
            if candidates:
                candidates = candidates.intersection(spatial_candidates)
            else:
                candidates = spatial_candidates
        
        # If no specific filters, return all commuters
        if not candidates and not any([query.depot_id, query.route_id, query.location]):
            candidates = set(self.commuters)
        
        # Sort by priority and wait time
        candidates_list = list(candidates)
        candidates_list.sort(key=lambda r: (-r.priority, -r.wait_time_minutes))
        
        return candidates_list
    
    def _calculate_distance(self, loc1: tuple, loc2: tuple) -> float:
        """Calculate distance between two locations in kilometers (Haversine)"""
        lat1, lon1 = math.radians(loc1[0]), math.radians(loc1[1])
        lat2, lon2 = math.radians(loc2[0]), math.radians(loc2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        return 6371 * c  # Earth radius in km
    
    def _cleanup_expired_reservations(self):
        """Remove expired commuter reservations"""
        active_commuters = []
        expired_count = 0
        
        for reservation in self.commuters:
            if reservation.is_expired:
                self._remove_from_indices(reservation)
                expired_count += 1
            else:
                active_commuters.append(reservation)
        
        self.commuters = active_commuters
        
        if expired_count > 0:
            logging.debug(f"🧹 Cleaned up {expired_count} expired reservations")
    
    def _calculate_recent_spawn_rate(self) -> float:
        """Calculate recent spawn rate (commuters per minute)"""
        if len(self.spawn_history) < 2:
            return 0.0
        
        # Look at last 10 entries
        recent_history = self.spawn_history[-10:]
        total_spawned = sum(h['spawned'] for h in recent_history)
        
        if len(recent_history) > 1:
            time_span = (recent_history[-1]['timestamp'] - recent_history[0]['timestamp']).total_seconds() / 60
            return total_spawned / max(1, time_span)
        
        return 0.0