import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

import unittest

class TestVehicleSimulator(unittest.TestCase):

    def test_simulator_module_imports(self):
        """Test if the simulator module can be imported."""
        try:
            import arknet_transit_simulator.simulator as sim_module
            self.assertIsNotNone(sim_module)
        except ImportError as e:
            self.fail(f"Failed to import simulator: {e}")

    def test_core_modules_exist(self):
        """Test if core modules exist."""
        try:
            from arknet_transit_simulator.core import dispatcher, depot_manager
            self.assertIsNotNone(dispatcher)
            self.assertIsNotNone(depot_manager)
        except ImportError as e:
            self.fail(f"Failed to import core modules: {e}")

    def test_speed_models_exist(self):
        """Test if speed models are available."""
        try:
            from arknet_transit_simulator.models import speed_models
            self.assertIsNotNone(speed_models)
        except ImportError as e:
            self.fail(f"Failed to import speed models: {e}")

if __name__ == "__main__":
    unittest.main()