#!/usr/bin/env python3
"""
Passenger Simulator - Main Entry Point

Usage: python passenger_simulator.py <route_id> <hour>
Example: python passenger_simulator.py 1B 8

This is the main entry point for passenger simulation using the comprehensive 
barbados_v3 model with time-smeared passenger generation.
"""

import sys
import os
import logging
from datetime import datetime

# Add the passenger_simulator to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main function for integrated time-smeared passenger generation"""
    
    if len(sys.argv) != 3:
        print("Usage: python passenger_simulator.py <route_id> <hour>")
        print("Example: python passenger_simulator.py 1B 8")
        sys.exit(1)
    
    try:
        route_id = sys.argv[1]
        hour = int(sys.argv[2])
        
        if not (0 <= hour <= 23):
            print("Error: Hour must be between 0 and 23")
            sys.exit(1)
        
        print(f"=" * 80)
        print(f"🚀 PASSENGER SIMULATOR - COMPREHENSIVE MODEL")
        print(f"=" * 80)
        print(f"Route: {route_id}")
        print(f"Hour: {hour}:00")
        print(f"Using: Comprehensive barbados_v3 model")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Import and initialize the time-smeared service
        from services.time_smeared_service import TimeSmearedPassengerService
        
        # Create the service with the comprehensive model
        service = TimeSmearedPassengerService("barbados_v3.json")
        
        # Generate time-smeared passengers
        passengers = service.generate_time_smeared_passengers(route_id, hour)
        
        # Print comprehensive summary
        service.print_passenger_summary(passengers)
        
        # Convert to standard passenger records if needed
        passenger_records = service.convert_to_passenger_records(passengers)
        
        print(f"\n✅ Generated {len(passenger_records)} passenger records")
        print(f"📊 Ready for integration with vehicle simulation system")
        
        # Optional: Save to file for further processing
        if passengers:
            import json
            
            # Convert to JSON-serializable format
            passengers_data = []
            for p in passengers:
                passengers_data.append({
                    "passenger_id": p.passenger_id,
                    "route_id": p.route_id,
                    "location_id": p.location_id,
                    "location_name": p.location_name,
                    "location_type": p.location_type,
                    "latitude": p.latitude,
                    "longitude": p.longitude,
                    "scheduled_arrival_time": p.scheduled_arrival_time.isoformat(),
                    "actual_arrival_time": p.actual_arrival_time.isoformat(),
                    "trip_purpose": p.trip_purpose,
                    "passenger_type": p.passenger_type,
                    "distance_to_next_location": p.distance_to_next_location
                })
            
            output_file = f"passengers_{route_id}_{hour:02d}h_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w') as f:
                json.dump({
                    "metadata": {
                        "route_id": route_id,
                        "hour": hour,
                        "generated_at": datetime.now().isoformat(),
                        "model_used": "barbados_v3.json",
                        "total_passengers": len(passengers_data)
                    },
                    "passengers": passengers_data
                }, f, indent=2)
            
            print(f"💾 Passenger data saved to: {output_file}")
        
    except ValueError:
        print("Error: Hour must be a valid integer")
        sys.exit(1)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the passenger_simulator directory")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()