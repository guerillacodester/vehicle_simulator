"""Test console launching to debug command generation."""
import subprocess
from pathlib import Path

# Test launching Strapi - try with call npm instead of just npm
strapi_path = Path(r"E:\projects\github\vehicle_simulator\arknet_fleet_manager\arknet-fleet-api")
title = "Strapi CMS Test"

# Try different approaches
print("=" * 70)
print("TEST 1: Using 'call npm run develop'")
print("=" * 70)
full_cmd1 = f'cd /d "{strapi_path}" && call npm run develop || pause'
print(f"Command: {full_cmd1}\n")
process1 = subprocess.Popen(
    ['cmd.exe', '/c', 'start', title + " (Test 1)", 'cmd.exe', '/k', full_cmd1]
)
print(f"Launched PID: {process1.pid}")

import time
time.sleep(2)

print("\n" + "=" * 70)
print("TEST 2: Using direct path - npm.cmd")
print("=" * 70)
full_cmd2 = f'cd /d "{strapi_path}" && npm.cmd run develop || pause'
print(f"Command: {full_cmd2}\n")
process2 = subprocess.Popen(
    ['cmd.exe', '/c', 'start', title + " (Test 2)", 'cmd.exe', '/k', full_cmd2]
)
print(f"Launched PID: {process2.pid}")

print("\nCheck which console window stays open...")

