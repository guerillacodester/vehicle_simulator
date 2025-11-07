import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest

class TestGPSCentCom(unittest.TestCase):

    def test_gpscentcom_import(self):
        """Test if the GPSCentCom module can be imported."""
        try:
            from gpscentcom_server import models
            self.assertTrue(hasattr(models, 'DeviceState'))
        except ImportError as e:
            self.fail(f"Failed to import gpscentcom_server: {e}")

    def test_device_state_model(self):
        """Test the DeviceState model structure."""
        try:
            from gpscentcom_server.models import DeviceState
            # Create a minimal DeviceState instance
            device = DeviceState(
                deviceId="test-device",
                route="1",
                vehicleReg="TEST-REG",
                driverId="drv-001",
                driverName={"first": "Test", "last": "Driver"},
                lat=13.2811,
                lon=-59.6464,
                speed=42.0,
                heading=143.5,
                timestamp="2025-11-07T00:00:00Z",
                lastSeen="2025-11-07T00:00:00Z"
            )
            self.assertEqual(device.deviceId, "test-device")
            self.assertEqual(device.lat, 13.2811)
        except Exception as e:
            self.fail(f"Failed to create DeviceState: {e}")

if __name__ == "__main__":
    unittest.main()
