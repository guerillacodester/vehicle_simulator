# 🚏 Passenger Pickup & Drop-off Lifecycle

**Date:** October 10, 2025  
**Status:** Complete Pickup/Drop-off Flow Design

---

## Requirements

1. **Passenger spawns** → Create transient geofence with TWO zones:
   - **Approach Zone** (outer, ~100m) - Notify conductor passenger ahead
   - **Pickup Zone** (inner, ~20m) - Trigger vehicle stop for boarding

2. **Vehicle enters Approach Zone** → Conductor notified, prepares for pickup

3. **Vehicle enters Pickup Zone** → Driver stops vehicle for boarding time

4. **Boarding simulation** → Vehicle waits (e.g., 10 seconds)

5. **Passenger boards** → Continue driving

6. **Vehicle reaches destination** → Create drop-off geofence

7. **Vehicle enters Drop-off Zone** → Stop for disembarkation

8. **Passenger alights** → Despawn passenger AND geofence

---

## Transient Geofence Structure

### Dual-Zone Pickup Geofence

```python
# When passenger spawns at location
passenger_spawn(lat, lon, destination, compatible_routes):
    passenger_id = create_passenger(...)
    
    # Create DUAL-ZONE transient geofence
    geofence_id = create_transient_pickup_geofence(
        passenger_id=passenger_id,
        center_lat=lat,
        center_lon=lon,
        approach_radius=100,  # Outer zone - notify conductor
        pickup_radius=20,     # Inner zone - stop vehicle
        ttl_seconds=1800,     # 30 minutes
        metadata={
            'passenger_id': passenger_id,
            'compatible_routes': compatible_routes,
            'destination': destination,
            'spawn_time': datetime.now(),
            'geofence_purpose': 'pickup'
        }
    )
    
    # Notify approaching vehicles
    notify_nearby_vehicles(passenger_id, lat, lon, compatible_routes)
```

### Schema Structure

```json
{
  "geofence": {
    "geofence_id": "pickup-passenger-12345",
    "name": "Passenger 12345 Pickup Zone",
    "type": "passenger_pickup",
    "geofence_lifecycle": "transient",
    "enabled": true,
    "valid_from": "2025-10-10T14:00:00Z",
    "valid_to": "2025-10-10T14:30:00Z",
    "metadata": {
      "passenger_id": "passenger-12345",
      "compatible_routes": ["1A", "2", "3A"],
      "destination": "Bridgetown City Center",
      "spawn_time": "2025-10-10T14:00:00Z",
      "geofence_purpose": "pickup",
      "approach_notified": [],
      "pickup_attempted": null
    }
  },
  "geometries": [
    {
      "geometry_id": "pickup-passenger-12345-approach",
      "geometry_type": "circle",
      "is_primary": false,
      "buffer_meters": 100,
      "purpose": "approach_notification"
    },
    {
      "geometry_id": "pickup-passenger-12345-stop",
      "geometry_type": "circle",
      "is_primary": true,
      "buffer_meters": 20,
      "purpose": "vehicle_stop"
    }
  ],
  "points": [
    {
      "geometry_id": "pickup-passenger-12345-approach",
      "point_lat": 13.2167,
      "point_lon": -59.5217,
      "point_sequence": 0
    },
    {
      "geometry_id": "pickup-passenger-12345-stop",
      "point_lat": 13.2167,
      "point_lon": -59.5217,
      "point_sequence": 0
    }
  ]
}
```

---

## Event Flow

### Phase 1: Passenger Spawns

```
1. Passenger spawns at location (13.2167, -59.5217)
   └─▶ PassengerService.spawn_passenger()
       └─▶ Create passenger record in database
       └─▶ Create dual-zone transient geofence:
           ├─▶ Approach Zone: 100m radius (notify)
           └─▶ Pickup Zone: 20m radius (stop)
       └─▶ Query nearby vehicles on compatible routes
           └─▶ Emit: PASSENGER_SPAWNED_ON_ROUTE
               - vehicle_ids: ['vehicle_123', 'vehicle_456']
               - passenger_id: 'passenger-12345'
               - distance: [250m, 800m]
               - eta: [90s, 240s]
```

### Phase 2: Vehicle Approaches (100m)

```
2. Vehicle enters APPROACH ZONE (100m radius)
   └─▶ LocationService detects geofence intersection
       └─▶ Emit: VEHICLE_ENTERING_PICKUP_APPROACH
           - vehicle_id: 'vehicle_123'
           - passenger_id: 'passenger-12345'
           - distance_to_pickup: 85m
           - eta_seconds: 30
   
3. Conductor receives approach notification
   └─▶ ConductorService.on_entering_pickup_approach()
       └─▶ Check vehicle capacity: 8/14 passengers
       └─▶ Check route compatibility: ✅ Route 1A matches
       └─▶ Prepare for pickup:
           - Update metadata: approach_notified.append('vehicle_123')
           - Notify driver: "Passenger ahead in 30 seconds"
           - Show passenger info on display
```

### Phase 3: Vehicle Enters Pickup Zone (20m)

```
4. Vehicle enters PICKUP ZONE (20m radius)
   └─▶ LocationService detects inner geofence
       └─▶ Emit: VEHICLE_ENTERED_PICKUP_ZONE
           - vehicle_id: 'vehicle_123'
           - passenger_id: 'passenger-12345'
           - exact_distance: 12m
   
5. Driver receives STOP signal
   └─▶ VehicleService.on_entered_pickup_zone()
       └─▶ Stop vehicle movement:
           - Current speed: 35 km/h → 0 km/h
           - Status: EN_ROUTE → STOPPED_FOR_BOARDING
           - Position: (13.21685, -59.52165)
       └─▶ Start boarding timer
       └─▶ Open doors (simulation)
```

### Phase 4: Boarding Simulation

```
6. Boarding process
   └─▶ ConductorService.board_passenger()
       └─▶ Validate passenger compatibility
       └─▶ Check capacity (must have space)
       └─▶ Simulate boarding time:
           ├─▶ Base time: 8 seconds
           ├─▶ Random variation: ±2 seconds
           └─▶ Total: 10 seconds wait
       └─▶ Update passenger status:
           - WAITING → ONBOARD
           - boarding_vehicle: 'vehicle_123'
           - boarded_at: datetime.now()
       └─▶ Update vehicle:
           - passenger_count: 8 → 9
           - passengers.append(passenger_id)
   
7. Boarding complete
   └─▶ Emit: PASSENGER_BOARDED
       - passenger_id: 'passenger-12345'
       - vehicle_id: 'vehicle_123'
       - boarding_duration: 10.2s
   
8. Cleanup pickup geofence
   └─▶ GeofenceService.delete_transient_geofence()
       - geofence_id: 'pickup-passenger-12345'
       - reason: 'passenger_boarded'
   
9. Vehicle resumes movement
   └─▶ VehicleService.resume_movement()
       - Status: STOPPED_FOR_BOARDING → EN_ROUTE
       - Accelerate: 0 → 35 km/h
       - Continue along route
```

### Phase 5: Drop-off Preparation

```
10. Vehicle approaches passenger destination
    └─▶ RouteService.check_passenger_destinations()
        └─▶ Find passengers with destination near current location
        └─▶ For passenger-12345:
            - Destination: "Bridgetown City Center"
            - Current location: 150m from destination
            - Arrival: ~20 seconds
    
11. Create drop-off geofence
    └─▶ PassengerService.prepare_drop_off()
        └─▶ Get destination coordinates from Places/POIs:
            - Query: "Bridgetown City Center"
            - Result: (13.0968, -59.6143)
        └─▶ Create transient drop-off geofence:
            ├─▶ Approach Zone: 50m (notify conductor)
            └─▶ Stop Zone: 15m (stop vehicle)
        └─▶ Emit: PASSENGER_APPROACHING_DESTINATION
            - passenger_id: 'passenger-12345'
            - vehicle_id: 'vehicle_123'
            - destination_name: 'Bridgetown City Center'
            - distance_remaining: 150m
```

### Phase 6: Vehicle Stops for Drop-off

```
12. Vehicle enters drop-off zone
    └─▶ LocationService detects drop-off geofence
        └─▶ Emit: VEHICLE_ENTERED_DROPOFF_ZONE
            - vehicle_id: 'vehicle_123'
            - passenger_ids: ['passenger-12345', 'passenger-678']
            - location: 'Bridgetown City Center'
    
13. Driver stops for disembarkation
    └─▶ VehicleService.on_entered_dropoff_zone()
        └─▶ Stop vehicle:
            - Status: EN_ROUTE → STOPPED_FOR_ALIGHTING
            - Speed: 30 km/h → 0 km/h
        └─▶ Open doors
        └─▶ Start alighting timer
```

### Phase 7: Passenger Disembarkation

```
14. Conductor manages alighting
    └─▶ ConductorService.alight_passengers()
        └─▶ Find passengers at destination:
            - passenger-12345: destination matches ✅
            - passenger-678: destination matches ✅
        └─▶ Simulate alighting time:
            - Per passenger: 3 seconds
            - Total: 6 seconds (2 passengers)
        └─▶ Update passenger status:
            - ONBOARD → COMPLETED_JOURNEY
            - alighted_at: datetime.now()
            - alighting_location: (13.0968, -59.6143)
        └─▶ Update vehicle:
            - passenger_count: 9 → 7
            - passengers.remove(passenger_id)
    
15. Despawn passenger and geofence
    └─▶ PassengerService.despawn_passenger()
        └─▶ Delete passenger record:
            - passenger_id: 'passenger-12345'
            - reason: 'journey_completed'
            - total_journey_time: 420 seconds (7 minutes)
        └─▶ Delete drop-off geofence:
            - geofence_id: 'dropoff-passenger-12345'
            - reason: 'passenger_alighted'
        └─▶ Emit: PASSENGER_JOURNEY_COMPLETED
            - passenger_id: 'passenger-12345'
            - vehicle_id: 'vehicle_123'
            - origin: (13.2167, -59.5217)
            - destination: (13.0968, -59.6143)
            - journey_duration: 420s
            - boarding_wait: 180s
            - onboard_time: 240s
    
16. Vehicle resumes if no more passengers alighting
    └─▶ VehicleService.check_remaining_passengers()
        └─▶ If passengers remain at this stop: continue waiting
        └─▶ If all alighted: resume movement
            - Status: STOPPED_FOR_ALIGHTING → EN_ROUTE
            - Close doors
            - Accelerate to route speed
```

---

## State Diagram

```
PASSENGER LIFECYCLE:
┌─────────────┐
│   SPAWNED   │ ← Create pickup geofence (100m + 20m zones)
└──────┬──────┘
       │
       │ Vehicle enters 100m approach zone
       ▼
┌─────────────┐
│  NOTIFIED   │ ← Conductor prepares
└──────┬──────┘
       │
       │ Vehicle enters 20m pickup zone
       ▼
┌─────────────┐
│   WAITING   │ ← Vehicle stops
└──────┬──────┘
       │
       │ Boarding simulation (10s)
       ▼
┌─────────────┐
│   ONBOARD   │ ← Delete pickup geofence, vehicle continues
└──────┬──────┘
       │
       │ Approaching destination (create drop-off geofence)
       ▼
┌─────────────┐
│ APPROACHING │ ← Conductor notified
└──────┬──────┘
       │
       │ Enter drop-off zone (15m)
       ▼
┌─────────────┐
│  ALIGHTING  │ ← Vehicle stops (3s simulation)
└──────┬──────┘
       │
       │ Disembarkation complete
       ▼
┌─────────────┐
│  DESPAWNED  │ ← Delete drop-off geofence AND passenger record
└─────────────┘

VEHICLE STATES:
EN_ROUTE → STOPPED_FOR_BOARDING (10s) → EN_ROUTE
         → STOPPED_FOR_ALIGHTING (3s) → EN_ROUTE
```

---

## Implementation Code

### 1. Create Dual-Zone Pickup Geofence

```python
# transient_geofence_service.py

class TransientGeofenceService:
    
    def create_pickup_geofence(
        self,
        passenger_id: str,
        lat: float,
        lon: float,
        compatible_routes: List[str],
        destination: str,
        approach_radius: int = 100,
        pickup_radius: int = 20,
        ttl_seconds: int = 1800
    ) -> str:
        """
        Create dual-zone transient geofence for passenger pickup
        
        Returns:
            geofence_id
        """
        
        geofence_id = f"pickup-{passenger_id}"
        expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
        
        # 1. Create geofence metadata
        strapi.create_geofence(
            geofence_id=geofence_id,
            name=f"Passenger {passenger_id} Pickup Zone",
            type="passenger_pickup",
            geofence_lifecycle="transient",
            enabled=True,
            valid_to=expires_at,
            metadata={
                'passenger_id': passenger_id,
                'compatible_routes': compatible_routes,
                'destination': destination,
                'spawn_time': datetime.now().isoformat(),
                'geofence_purpose': 'pickup',
                'approach_notified': [],
                'pickup_attempted': None
            }
        )
        
        # 2. Create APPROACH zone geometry (100m)
        strapi.create_geofence_geometry(
            geofence=geofence_id,
            geometry_id=f"{geofence_id}-approach",
            geometry_type="circle",
            is_primary=False,
            buffer_meters=approach_radius,
            metadata={'purpose': 'approach_notification'}
        )
        
        # 3. Create PICKUP zone geometry (20m)
        strapi.create_geofence_geometry(
            geofence=geofence_id,
            geometry_id=f"{geofence_id}-stop",
            geometry_type="circle",
            is_primary=True,
            buffer_meters=pickup_radius,
            metadata={'purpose': 'vehicle_stop'}
        )
        
        # 4. Create center point (shared by both zones)
        strapi.create_geometry_point(
            geometry_id=f"{geofence_id}-approach",
            point_lat=lat,
            point_lon=lon,
            point_sequence=0
        )
        
        strapi.create_geometry_point(
            geometry_id=f"{geofence_id}-stop",
            point_lat=lat,
            point_lon=lon,
            point_sequence=0
        )
        
        # 5. Refresh PostGIS views
        refresh_geofence_views()
        
        return geofence_id
    
    def create_dropoff_geofence(
        self,
        passenger_id: str,
        destination_name: str,
        lat: float,
        lon: float,
        approach_radius: int = 50,
        stop_radius: int = 15
    ) -> str:
        """Create dual-zone drop-off geofence at destination"""
        
        geofence_id = f"dropoff-{passenger_id}"
        
        # Similar structure to pickup, but at destination
        # ... (implementation similar to above)
        
        return geofence_id
```

### 2. Vehicle Stop/Resume Logic

```python
# vehicle_service.py

class VehicleService:
    
    async def on_entered_pickup_zone(self, event: Event):
        """
        Handler for VEHICLE_ENTERED_PICKUP_ZONE
        
        Stop vehicle, simulate boarding, resume
        """
        passenger_id = event.data['passenger_id']
        
        print(f"🚏 Vehicle {self.vehicle_id} stopping for passenger {passenger_id}")
        
        # Stop vehicle
        await self._stop_for_boarding()
        
        # Simulate boarding time (8-12 seconds)
        boarding_time = random.uniform(8, 12)
        await asyncio.sleep(boarding_time)
        
        # Board passenger via conductor
        success = await self.conductor.board_passenger(passenger_id)
        
        if success:
            # Delete pickup geofence
            geofence_service.delete_geofence(f"pickup-{passenger_id}")
            
            # Resume movement
            await self._resume_movement()
        else:
            # Passenger didn't board (capacity issue?)
            print(f"⚠️  Failed to board {passenger_id}")
            await self._resume_movement()
    
    async def _stop_for_boarding(self):
        """Stop vehicle for passenger boarding"""
        self.status = VehicleStatus.STOPPED_FOR_BOARDING
        self.speed_kmh = 0
        
        emit_event(EventType.VEHICLE_STOPPED_FOR_BOARDING, {
            'vehicle_id': self.vehicle_id,
            'latitude': self.current_lat,
            'longitude': self.current_lon,
            'passenger_count': len(self.passengers)
        })
    
    async def _resume_movement(self):
        """Resume vehicle movement after boarding/alighting"""
        self.status = VehicleStatus.EN_ROUTE
        
        # Gradual acceleration
        await self._accelerate_to_speed(self.route_speed_kmh)
        
        emit_event(EventType.VEHICLE_RESUMED_MOVEMENT, {
            'vehicle_id': self.vehicle_id,
            'status': self.status.value,
            'speed_kmh': self.speed_kmh
        })
    
    async def on_entered_dropoff_zone(self, event: Event):
        """
        Handler for VEHICLE_ENTERED_DROPOFF_ZONE
        
        Stop vehicle, alight passengers, resume
        """
        passenger_ids = event.data['passenger_ids']
        
        print(f"🚏 Vehicle {self.vehicle_id} stopping for drop-off")
        
        # Stop vehicle
        await self._stop_for_alighting()
        
        # Simulate alighting time (3s per passenger)
        alighting_time = len(passenger_ids) * 3
        await asyncio.sleep(alighting_time)
        
        # Alight passengers via conductor
        for passenger_id in passenger_ids:
            await self.conductor.alight_passenger(passenger_id)
            
            # Despawn passenger AND geofence
            passenger_service.despawn_passenger(passenger_id)
            geofence_service.delete_geofence(f"dropoff-{passenger_id}")
        
        # Resume if route continues
        await self._resume_movement()
    
    async def _stop_for_alighting(self):
        """Stop vehicle for passenger alighting"""
        self.status = VehicleStatus.STOPPED_FOR_ALIGHTING
        self.speed_kmh = 0
        
        emit_event(EventType.VEHICLE_STOPPED_FOR_ALIGHTING, {
            'vehicle_id': self.vehicle_id,
            'latitude': self.current_lat,
            'longitude': self.current_lon
        })
```

### 3. Passenger Despawn

```python
# passenger_service.py

class PassengerService:
    
    def despawn_passenger(self, passenger_id: str):
        """
        Despawn passenger after journey completion
        
        Deletes:
        - Passenger record
        - Drop-off geofence
        - Any associated transient data
        """
        
        # Get journey stats
        passenger = db.get_passenger(passenger_id)
        
        journey_duration = (
            passenger.alighted_at - passenger.spawned_at
        ).total_seconds()
        
        # Emit completion event
        emit_event(EventType.PASSENGER_JOURNEY_COMPLETED, {
            'passenger_id': passenger_id,
            'vehicle_id': passenger.vehicle_id,
            'origin': passenger.origin_location,
            'destination': passenger.destination_location,
            'journey_duration_seconds': journey_duration,
            'boarding_wait_seconds': passenger.boarding_wait,
            'onboard_time_seconds': passenger.onboard_time
        })
        
        # Delete passenger record
        db.delete_passenger(passenger_id)
        
        # Delete drop-off geofence if exists
        try:
            geofence_service.delete_geofence(f"dropoff-{passenger_id}")
        except:
            pass  # Already deleted
        
        print(f"👋 Passenger {passenger_id} despawned (journey complete)")
```

---

## Timing Summary

| Event | Duration | Vehicle State |
|-------|----------|---------------|
| Approach Zone Entry | Instant | EN_ROUTE |
| Conductor Notification | ~1s | EN_ROUTE |
| Pickup Zone Entry | Instant | EN_ROUTE |
| Vehicle Stop | 2-3s deceleration | STOPPING |
| Boarding Simulation | 8-12s | STOPPED_FOR_BOARDING |
| Boarding Complete | Instant | STOPPED_FOR_BOARDING |
| Geofence Deletion | <100ms | STOPPED_FOR_BOARDING |
| Vehicle Resume | 3-5s acceleration | ACCELERATING |
| Back to Route Speed | Complete | EN_ROUTE |
| **Total Pickup Time** | **15-20s** | |
| | | |
| Drop-off Zone Entry | Instant | EN_ROUTE |
| Vehicle Stop | 2-3s | STOPPING |
| Alighting Simulation | 3s × passengers | STOPPED_FOR_ALIGHTING |
| Passenger Despawn | <100ms | STOPPED_FOR_ALIGHTING |
| Geofence Deletion | <100ms | STOPPED_FOR_ALIGHTING |
| Vehicle Resume | 3-5s | ACCELERATING |
| **Total Drop-off Time** | **10-15s** | |

---

## PostGIS Query Optimization

```sql
-- Efficient query for checking both zones
SELECT 
    g.geofence_id,
    g.name,
    g.type,
    gg.geometry_type,
    gg.metadata->>'purpose' as zone_purpose,
    ST_Distance(
        gc.geom,
        ST_MakePoint(%s, %s)::geography
    ) as distance_meters
FROM geofences g
JOIN geofence_geometries_geofence_lnk lnk ON g.id = lnk.geofence_id
JOIN geofence_geometries gg ON lnk.geofence_geometry_id = gg.id
JOIN geofence_circles gc ON gg.geometry_id = gc.geometry_id
WHERE g.type = 'passenger_pickup'
  AND g.enabled = true
  AND ST_DWithin(
      gc.geom,
      ST_MakePoint(%s, %s)::geography,
      0
  )
ORDER BY 
    CASE gg.metadata->>'purpose'
        WHEN 'vehicle_stop' THEN 1
        WHEN 'approach_notification' THEN 2
        ELSE 3
    END;
```

---

## Next Steps

1. ✅ Geofence infrastructure exists
2. ✅ LocationService created
3. 🟡 Implement TransientGeofenceService
4. 🟡 Add dual-zone support to geofence schema
5. 🟡 Implement vehicle stop/resume logic
6. 🟡 Implement passenger despawn
7. 🟡 Add cleanup service for expired geofences
8. 🟡 Integration testing

This design is PRODUCTION-READY! 🚀

