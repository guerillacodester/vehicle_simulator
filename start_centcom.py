import sys
import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description="CentCom cross-platform launcher")
parser.add_argument("mode", choices=["console", "service"], default="console", nargs="?", help="Launch mode: console or service")
parser.add_argument("config", default="config.ini", nargs="?", help="Path to config file")
args = parser.parse_args()

PYTHON_BIN = sys.executable
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(PROJECT_ROOT, args.config)

os.chdir(PROJECT_ROOT)

cmd = [PYTHON_BIN, "-m", "gpscentcom_server", "--config", CONFIG_PATH]

if args.mode == "console":
    print(f"Launching CentCom in CONSOLE mode with {CONFIG_PATH}")
    sys.exit(subprocess.call(cmd))
else:
    print(f"Launching CentCom as SERVICE with {CONFIG_PATH}")
    if os.name == "nt":
        # Windows: run in background, redirect output
        subprocess.Popen(cmd, stdout=open("centcom.log", "a"), stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    else:
        # Linux/macOS: run in background, redirect output
        subprocess.Popen(cmd, stdout=open("centcom.log", "a"), stderr=subprocess.STDOUT)
    print("CentCom started as background service. Logs: centcom.log")
    sys.exit(0)
