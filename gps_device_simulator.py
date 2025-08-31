from datetime import datetime, timedelta, timezone
import os, time, configparser
from vehicle_factory.vehicle.gps_device.device import GPSDevice

def main():
    # Load secrets
    auth_token = os.getenv("AUTH_TOKEN", "")
    interval = float(os.getenv("UPDATE_INTERVAL", 1.0))

    # Load server URLs from config.ini
    config = configparser.ConfigParser()
    config.read("config.ini")
    server_url = config.get("server", "ws_url", fallback="ws://localhost:5000/")

    # Explicitly pass unique device_id
    gps = GPSDevice("bus-1203", server_url, auth_token, method="ws", interval=interval)

    gps.on()

    # Feed dummy telemetry
    for d in [
            {
                "lat": 13.2810,
                "lon": -59.6463,
                "speed": 42.0,
                "heading": 143.5,
                "route": "1",
                "vehicle_reg": "ZRTEST1",
                "driver_id": "drv-ZRTEST1",
                "driver_name": {"first": "Sim", "last": "Tester"},
                "ts": datetime.now(timezone.utc).isoformat(),
            },
            {
                "lat": 13.2811,
                "lon": -59.6464,
                "speed": 45.0,
                "heading": 144.0,
                "route": "1",
                "vehicle_reg": "ZRTEST1",
                "driver_id": "drv-ZRTEST1",
                "driver_name": {"first": "Sim", "last": "Tester"},
                "ts": (datetime.now(timezone.utc) + timedelta(seconds=1)).isoformat(),
            },
        ]:
        gps.buffer.write(d)
        time.sleep(0.5)

    time.sleep(2)  # let worker flush
    gps.off()

if __name__ == "__main__":
    main()
