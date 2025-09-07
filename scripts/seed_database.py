import os
import sys

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from config.database import get_db_config, get_ssh_tunnel
from utils.seeder import TransitSeeder

def main():
    # Start SSH tunnel
    tunnel = get_ssh_tunnel()
    tunnel.start()

    try:
        # Get DB config with tunnel
        db_params = get_db_config(tunnel)
        
        # Initialize seeder
        seeder = TransitSeeder(db_params)
        
        print("Seeding vehicles...")
        vehicle_ids = seeder.seed_vehicles(50)
        
        print("Seeding complete!")
        
    finally:
        tunnel.stop()

if __name__ == "__main__":
    main()