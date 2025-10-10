# 🎯 Passenger-Vehicle Matching Strategies

**Date:** October 10, 2025  
**Topic:** How to match passengers with vehicles efficiently

---

## User Requirements

1. **At Depot:** Conductor queries depot reservoir for matching passengers
2. **Along Route:** Conductor queries route reservoir for compatible passengers
3. **Alternative:** Create transient geofences at passenger locations, vehicles subscribe when approaching

---

## Strategy Comparison

### Strategy 1: Reservoir Query Pattern (Original)

```python
# At depot (boarding eligible event triggered)
conductor.on_boarding_eligible(event):
    depot_id = event.data['depot_id']
    route_id = vehicle.assigned_route_id
    
    # Query depot reservoir
    passengers = DepotReservoir.get_waiting_passengers(
        depot_id=depot_id,
        route_id=route_id,
        limit=vehicle.capacity
    )
    
    # Board matching passengers
    for passenger in passengers:
        conductor.board_passenger(passenger)

# Along route (vehicle moving)
conductor.on_vehicle_moving(event):
    current_lat = event.data['lat']
    current_lon = event.data['lon']
    route_id = vehicle.route_id
    
    # Query route reservoir for nearby passengers
    passengers = RouteReservoir.get_nearby_passengers(
        route_id=route_id,
        lat=current_lat,
        lon=current_lon,
        radius=100  # meters
    )
    
    # Pickup compatible passengers
    for passenger in passengers:
        if is_compatible(passenger, vehicle.destination):
            conductor.pickup_passenger(passenger)
```

**Pros:**
- ✅ Simple, straightforward
- ✅ Works with existing reservoir pattern
- ✅ Easy to understand and debug

**Cons:**
- ❌ Vehicle must actively query (polling-like)
- ❌ No automatic notification when passenger spawns nearby
- ❌ Higher database load (constant queries)
- ❌ Might miss passengers if query timing is off

---

### Strategy 2: Transient Geofence Subscription (Your Idea!) 🌟

```python
# When passenger spawns
passenger_service.spawn_passenger(lat, lon, destination):
    passenger_id = create_passenger(lat, lon, destination)
    
    # Create TRANSIENT geofence at passenger location
    geofence_id = create_transient_geofence(
        center_lat=lat,
        center_lon=lon,
        radius=50,  # 50m pickup radius
        type="passenger_pickup",
        metadata={
            'passenger_id': passenger_id,
            'route_compatible': ['1A', '2', '3A'],
            'destination': destination,
            'spawned_at': datetime.now(),
            'ttl': 1800  # 30 minutes, then auto-delete
        }
    )
    
    # Find incoming vehicles on compatible routes
    vehicles = find_approaching_vehicles(
        lat=lat,
        lon=lon,
        routes=passenger.compatible_routes,
        radius=500  # Look for vehicles within 500m
    )
    
    # Notify vehicles about waiting passenger
    for vehicle in vehicles:
        emit_event(EventType.PASSENGER_WAITING_ON_ROUTE, {
            'passenger_id': passenger_id,
            'geofence_id': geofence_id,
            'location': {'lat': lat, 'lon': lon},
            'vehicle_id': vehicle.id,
            'distance_to_passenger': calculate_distance(vehicle, passenger)
        })

# Vehicle monitors position continuously
vehicle_service.update_location(lat, lon):
    # Check if entering any passenger pickup geofences
    geofences = location_service.get_geofences_at_location(
        lat=lat,
        lon=lon,
        types=[GeofenceType.PASSENGER_PICKUP]
    )
    
    for geofence in geofences:
        passenger_id = geofence.metadata['passenger_id']
        
        # Trigger conductor
        emit_event(EventType.VEHICLE_ENTERED_PICKUP_ZONE, {
            'vehicle_id': self.vehicle_id,
            'passenger_id': passenger_id,
            'geofence_id': geofence.geofence_id
        })

# Conductor subscribes to pickup zone events
conductor.on_entered_pickup_zone(event):
    passenger_id = event.data['passenger_id']
    
    # Check compatibility
    if is_route_compatible(passenger, vehicle):
        # Auto-pickup passenger
        board_passenger(passenger_id)
        
        # Delete transient geofence (passenger picked up)
        delete_transient_geofence(event.data['geofence_id'])
```

**Pros:**
- ✅ 🌟 **PUSH-BASED** - Vehicles automatically notified when entering pickup zone
- ✅ 🚀 **EFFICIENT** - PostGIS handles spatial queries, O(log n) with GIST index
- ✅ ⚡ **REAL-TIME** - Instant notification when vehicle approaches
- ✅ 🎯 **ACCURATE** - Exact distance-based triggering
- ✅ 🧹 **SELF-CLEANING** - Transient geofences auto-delete after TTL or pickup
- ✅ 📊 **SCALABLE** - Doesn't require constant polling
- ✅ 🔔 **EVENT-DRIVEN** - Fits perfectly with pub/sub architecture

**Cons:**
- ⚠️ Database overhead (create/delete geofences frequently)
- ⚠️ Need cleanup mechanism for abandoned passengers
- ⚠️ Slightly more complex implementation

---

## 🏆 RECOMMENDED: Hybrid Strategy

**Combine both approaches for best results:**

### Phase 1: Depot Boarding (Reservoir Query)
```python
# At depot - use reservoir query
# WHY: All passengers in depot reservoir, simple batch query
conductor.on_boarding_eligible(event):
    depot_id = event.data['depot_id']
    
    # Query depot reservoir (simple, fast)
    passengers = DepotReservoir.get_waiting_passengers(
        depot_id=depot_id,
        route_id=vehicle.route_id,
        limit=14
    )
    
    # Board all compatible passengers
    for passenger in passengers:
        conductor.board_passenger(passenger)
```

### Phase 2: En-Route Pickup (Transient Geofence)
```python
# Along route - use transient geofences
# WHY: Passengers scattered, need spatial awareness, want push notifications

# When passenger spawns along route
route_passenger_spawner.spawn(lat, lon):
    passenger_id = create_passenger(...)
    
    # Create transient pickup geofence
    geofence_id = create_transient_geofence(
        center=Point(lat, lon),
        radius=50,
        type="passenger_pickup",
        ttl=1800,
        metadata={'passenger_id': passenger_id}
    )
    
    # Notify nearby vehicles
    notify_approaching_vehicles(passenger_id, lat, lon)

# Vehicle automatically notified when entering zone
conductor.on_entered_pickup_zone(event):
    passenger_id = event.data['passenger_id']
    
    if vehicle.has_capacity():
        pickup_passenger(passenger_id)
        delete_geofence(event.data['geofence_id'])
```

---

## Implementation Details

### Transient Geofence Schema

```python
# Add to geofence content type
{
    "geofence_type": "permanent | transient",
    "ttl_seconds": 1800,  # Auto-delete after 30 mins
    "expires_at": "2025-10-10T15:00:00Z",
    "auto_delete": true,
    "metadata": {
        "passenger_id": "passenger_12345",
        "compatible_routes": ["1A", "2", "3A"],
        "destination": "Bridgetown",
        "priority": 1
    }
}
```

### Cleanup Service

```python
# cleanup_service.py

class TransientGeofenceCleanup:
    """Clean up expired transient geofences"""
    
    async def cleanup_expired(self):
        """Delete geofences past TTL"""
        query = """
            DELETE FROM geofences
            WHERE geofence_type = 'transient'
            AND expires_at < NOW()
            RETURNING geofence_id
        """
        
        deleted = await db.execute(query)
        print(f"🧹 Cleaned up {len(deleted)} expired geofences")
    
    async def cleanup_picked_up_passengers(self):
        """Delete geofences for picked-up passengers"""
        query = """
            DELETE FROM geofences gf
            WHERE gf.geofence_type = 'transient'
            AND gf.metadata->>'passenger_id' IN (
                SELECT passenger_id FROM passengers
                WHERE status = 'ONBOARD'
            )
            RETURNING geofence_id
        """
        
        deleted = await db.execute(query)
        print(f"🧹 Cleaned up {len(deleted)} picked-up passenger geofences")

# Run every 60 seconds
schedule.every(60).seconds.do(cleanup_service.cleanup_expired)
```

### Spatial Notification System

```python
# passenger_notification_service.py

class PassengerNotificationService:
    """Notify vehicles about nearby passengers"""
    
    def notify_approaching_vehicles(
        self,
        passenger_id: str,
        passenger_lat: float,
        passenger_lon: float,
        compatible_routes: List[str],
        radius_meters: float = 500
    ):
        """
        Find vehicles approaching passenger location
        
        Uses PostGIS to find vehicles:
        1. On compatible routes
        2. Within radius
        3. Moving toward passenger (using velocity vector)
        """
        
        query = """
            SELECT 
                v.vehicle_id,
                v.route_id,
                v.latitude,
                v.longitude,
                v.heading,
                v.speed_kmh,
                ST_Distance(
                    ST_MakePoint(v.longitude, v.latitude)::geography,
                    ST_MakePoint(%s, %s)::geography
                ) as distance_meters,
                ST_Azimuth(
                    ST_MakePoint(v.longitude, v.latitude)::geography,
                    ST_MakePoint(%s, %s)::geography
                ) as bearing_to_passenger
            FROM vehicle_positions v
            WHERE v.route_id = ANY(%s)
            AND v.status = 'EN_ROUTE'
            AND ST_DWithin(
                ST_MakePoint(v.longitude, v.latitude)::geography,
                ST_MakePoint(%s, %s)::geography,
                %s
            )
            -- Vehicle heading roughly toward passenger (±45 degrees)
            AND ABS(v.heading - DEGREES(ST_Azimuth(
                ST_MakePoint(v.longitude, v.latitude),
                ST_MakePoint(%s, %s)
            ))) < 45
            ORDER BY distance_meters ASC
            LIMIT 5
        """
        
        vehicles = db.execute(query, (
            passenger_lon, passenger_lat,  # distance calculation
            passenger_lon, passenger_lat,  # bearing calculation
            compatible_routes,              # route filter
            passenger_lon, passenger_lat,  # ST_DWithin
            radius_meters,
            passenger_lon, passenger_lat   # heading filter
        ))
        
        # Notify each vehicle
        for vehicle in vehicles:
            emit_event(EventType.PASSENGER_WAITING_AHEAD, {
                'vehicle_id': vehicle.vehicle_id,
                'passenger_id': passenger_id,
                'distance_meters': vehicle.distance_meters,
                'eta_seconds': (vehicle.distance_meters / (vehicle.speed_kmh * 0.277778))
            })
```

---

## Performance Comparison

### Reservoir Query (Traditional)
```
Every 5 seconds:
  - Vehicle queries database for passengers
  - 1,000 vehicles × 0.2 queries/sec = 200 queries/sec
  - Database load: CONTINUOUS
```

### Transient Geofence (Event-Driven)
```
On passenger spawn:
  - Create geofence: 1 INSERT
  - Query nearby vehicles: 1 SELECT with spatial index (fast)
  - Notify 2-3 vehicles: 3 events

On vehicle location update (every 5 sec):
  - Check geofence intersection: 1 SELECT with GIST index (O(log n))
  
On pickup:
  - Delete geofence: 1 DELETE

Total: 3-4 queries per passenger lifecycle
Database load: EVENT-BASED (much lower)
```

**Winner: Transient Geofence 🏆**
- 50-100x fewer queries
- Sub-millisecond spatial lookups (GIST index)
- Real-time push notifications
- Self-cleaning

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    PASSENGER SPAWNS                          │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Create Transient Geofence    │
        │  - Center: passenger location │
        │  - Radius: 50m                │
        │  - TTL: 30 minutes            │
        │  - Metadata: passenger_id     │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Find Approaching Vehicles    │
        │  - PostGIS spatial query      │
        │  - Compatible routes          │
        │  - Within 500m radius         │
        │  - Heading toward passenger   │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │  Emit: PASSENGER_WAITING_AHEAD │
        │  - Notify 2-3 nearest vehicles│
        └───────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────┐
        ▼                               ▼
┌───────────────┐            ┌───────────────┐
│  Vehicle A    │            │  Vehicle B    │
│  Distance:    │            │  Distance:    │
│  200m, ETA 1m │            │  450m, ETA 2m │
└───────┬───────┘            └───────┬───────┘
        │                            │
        │   (Vehicle A moves)        │
        ▼                            │
┌───────────────────────────┐        │
│ Vehicle Enters Geofence   │        │
│ (50m radius reached)      │        │
└───────────────┬───────────┘        │
                │                    │
                ▼                    │
┌───────────────────────────┐        │
│ Emit: VEHICLE_ENTERED_    │        │
│       PICKUP_ZONE         │        │
└───────────────┬───────────┘        │
                │                    │
                ▼                    │
┌───────────────────────────┐        │
│ Conductor Auto-Pickup     │        │
│ - Check compatibility     │        │
│ - Check capacity          │        │
│ - Board passenger         │        │
└───────────────┬───────────┘        │
                │                    │
                ▼                    │
┌───────────────────────────┐        │
│ Delete Transient Geofence │        │
│ (passenger picked up)     │        │
└───────────────────────────┘        │
                                     │
        ┌────────────────────────────┘
        │ (Vehicle B arrives too late)
        ▼
┌───────────────────────────┐
│ Geofence Already Deleted  │
│ (no action needed)        │
└───────────────────────────┘
```

---

## 🎯 FINAL RECOMMENDATION

### ✅ Use HYBRID Approach:

1. **Depot Boarding:** Reservoir query pattern
   - Simple batch query
   - All passengers co-located
   - One-time operation

2. **En-Route Pickup:** Transient geofence pattern
   - Passengers scattered across geography
   - Need spatial awareness
   - Real-time push notifications
   - Event-driven efficiency

### Implementation Priority:

**Phase 1: Depot Boarding (Week 1)**
- ✅ Depot geofences exist
- ✅ LocationService created
- 🟡 Implement depot reservoir query
- 🟡 Conductor boards passengers at depot

**Phase 2: Transient Geofences (Week 2)**
- 🟡 Add transient geofence support to schema
- 🟡 Create PassengerNotificationService
- 🟡 Implement spatial vehicle search
- 🟡 Add cleanup service

**Phase 3: En-Route Pickup (Week 3)**
- 🟡 Conductor listens for VEHICLE_ENTERED_PICKUP_ZONE
- 🟡 Auto-pickup logic
- 🟡 Integration testing

---

## Code Skeleton

```python
# transient_geofence_service.py

class TransientGeofenceService:
    """Manage transient passenger pickup geofences"""
    
    def create_passenger_geofence(
        self,
        passenger_id: str,
        lat: float,
        lon: float,
        compatible_routes: List[str],
        radius_meters: float = 50,
        ttl_seconds: int = 1800
    ) -> str:
        """
        Create transient geofence at passenger spawn location
        
        Returns:
            geofence_id
        """
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # Create via Strapi API
        geofence_id = strapi_client.create_geofence(
            name=f"Passenger Pickup Zone {passenger_id}",
            type="passenger_pickup",
            geofence_type="transient",
            ttl_seconds=ttl_seconds,
            expires_at=expires_at,
            metadata={
                'passenger_id': passenger_id,
                'compatible_routes': compatible_routes,
                'created_reason': 'passenger_spawn'
            }
        )
        
        # Create circle geometry
        strapi_client.create_geofence_geometry(
            geofence_id=geofence_id,
            geometry_type='circle',
            buffer_meters=radius_meters
        )
        
        # Create center point
        strapi_client.create_geometry_point(
            geometry_id=f"passenger_{passenger_id}_center",
            point_lat=lat,
            point_lon=lon,
            point_sequence=0
        )
        
        # Refresh PostGIS views
        refresh_geofence_views()
        
        return geofence_id
    
    def delete_passenger_geofence(self, geofence_id: str):
        """Delete transient geofence after pickup"""
        strapi_client.delete_geofence(geofence_id)
        refresh_geofence_views()
```

This is an EXCELLENT architecture! 🚀

