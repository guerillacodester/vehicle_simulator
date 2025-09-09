"""
Usage Examples: How to inject real telemetry data into RxTx buffer
----------------------------------------------------------------

Replace simulated data with real data by using these simple patterns.
"""

# Example 1: Replace simulator's data generation
def replace_simulator_data_source():
    """
    Modify the simulator to use real data instead of generating fake data
    """
    
    # In simulator.py, replace the _transmit_gps_data method:
    
    # OLD (simulated):
    # gps_data = {
    #     "lat": vehicle.lat,
    #     "lon": vehicle.lng,
    #     "speed": vehicle.speed,
    #     # ... simulated values
    # }
    
    # NEW (real data):
    # Get real GPS data from your source
    real_gps_data = get_real_gps_data()  # Your function to get real data
    
    if real_gps_data:
        # Use existing buffer write - no changes needed!
        vehicle.gps_device.buffer.write(real_gps_data)


# Example 2: Direct buffer injection
def direct_buffer_injection_example():
    """
    Directly inject data into any GPS device buffer
    """
    from world.vehicle_simulator.adapters.data_injectors import SerialDataInjector
    
    # Get reference to existing GPS device buffer
    gps_device = vehicle.gps_device  # From your existing setup
    
    # Start injecting real data
    injector = SerialDataInjector(
        rxtx_buffer=gps_device.buffer,  # Use existing buffer!
        port="COM3",  # Your GPS device port
        baudrate=9600
    )
    
    injector.start()
    
    # The GPS device will automatically transmit whatever is in the buffer
    # No other changes needed!


# Example 3: Custom data source
def custom_data_source_example():
    """
    Use any data source - the key is just calling buffer.write()
    """
    
    def my_gps_reader():
        # Your custom GPS reading logic
        return {
            "lat": 13.2810,
            "lon": -59.6463,
            "speed": 45.0,
            "heading": 180.0,
            "route": "R001",
            "vehicle_reg": "BUS001",
            "driver_id": "drv-001",
            "driver_name": {"first": "John", "last": "Driver"},
            "ts": "2025-09-09T12:00:00Z"
        }
    
    # In your main loop or thread:
    while running:
        real_data = my_gps_reader()
        if real_data:
            # Just write to the buffer - GPS device handles the rest!
            gps_device.buffer.write(real_data)
        time.sleep(1.0)


# Example 4: Modify existing simulator
def modify_simulator_for_real_data():
    """
    Simple modification to existing simulator.py
    """
    
    # Add this to simulator.py __init__:
    # self.real_data_source = YourDataSource()  # Serial, file, network, etc.
    
    # Modify _transmit_gps_data method:
    def _transmit_gps_data(self, vehicle):
        try:
            # Instead of simulated data, get real data
            real_data = self.real_data_source.get_latest_data()
            
            if real_data:
                # Same format as before - just real values!
                gps_data = {
                    "lat": real_data.latitude,
                    "lon": real_data.longitude,
                    "speed": real_data.speed,
                    "heading": real_data.heading,
                    "route": vehicle.route_id,
                    "vehicle_reg": vehicle.vehicle_id,
                    "driver_id": f"drv-{vehicle.vehicle_id}",
                    "driver_name": {"first": "Real", "last": "Driver"},
                    "ts": real_data.timestamp,
                }
                
                # Same buffer write - no changes to GPS device needed!
                vehicle.gps_device.buffer.write(gps_data)
                
        except Exception as e:
            print(f"⚠️ Real GPS data failed: {e}")


# Example 5: Background data injection
def background_injection_example():
    """
    Run real data injection in background while keeping simulator structure
    """
    import threading
    
    def background_gps_injection(gps_buffer):
        while True:
            try:
                # Read from your GPS source
                real_data = read_from_serial_port()  # Your implementation
                
                if real_data:
                    gps_buffer.write(real_data)
                    
                time.sleep(0.5)  # Adjust based on your GPS update rate
                
            except Exception as e:
                print(f"GPS injection error: {e}")
                time.sleep(1.0)
    
    # Start background injection
    injection_thread = threading.Thread(
        target=background_gps_injection, 
        args=(gps_device.buffer,), 
        daemon=True
    )
    injection_thread.start()
    
    # Your existing code continues unchanged!
