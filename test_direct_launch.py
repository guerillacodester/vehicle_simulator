"""Direct test of the exact command that should work."""
import subprocess
import sys
from pathlib import Path

print("Testing direct console launch...")
print(f"Python executable: {sys.executable}")
print()

# Test 1: Launch Strapi exactly as old launcher does
print("=" * 70)
print("TEST: Launching Strapi")
print("=" * 70)

strapi_path = Path(r"E:\projects\github\vehicle_simulator\arknet_fleet_manager\arknet-fleet-api")
base_cmd = ['npm', 'run', 'develop']
cmd_str = ' '.join(base_cmd)
title = "Strapi-CMS"

print(f"Command: {base_cmd}")
print(f"Command string: {cmd_str}")
print(f"Working directory: {strapi_path}")
print()

full_args = [
    "cmd.exe",
    "/c",
    "start",
    title,
    "cmd.exe",
    "/k",
    f"cd /d {strapi_path} && {cmd_str} || pause"
]

print("Full Popen args:")
for i, arg in enumerate(full_args):
    print(f"  [{i}] {repr(arg)}")
print()

print("Launching...")
process = subprocess.Popen(full_args, cwd=strapi_path)
print(f"✅ Process created, PID: {process.pid}")
print()
print("Did a new console window open with Strapi starting?")
