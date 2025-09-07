#!/usr/bin/env python
"""
Run main.py - Executable launcher
"""
import subprocess
import sys
import os

# Get the directory of this script
script_dir = os.path.dirname(os.path.abspath(__file__))
main_py_path = os.path.join(script_dir, "main.py")

# Run main.py with the current Python interpreter
try:
    subprocess.run([sys.executable, main_py_path] + sys.argv[1:])
except KeyboardInterrupt:
    print("\n🛑 Server stopped by user")
except Exception as e:
    print(f"❌ Error running main.py: {e}")
