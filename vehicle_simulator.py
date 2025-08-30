import argparse
from simulation.simulator import simulate_movement

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate vehicle movement along a route.")
    parser.add_argument('--route', type=str, required=True, help="Path to the GeoJSON file with route coordinates.")
    parser.add_argument('--tick', type=float, default=0.1, help="Tick speed in seconds (real-time speed).")
    args = parser.parse_args()

    simulate_movement(args.route, args.tick, "kinematic")
