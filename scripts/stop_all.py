#!/usr/bin/env python3
"""
ArkNet Host Server - Stop All Services
Cross-platform shutdown script for Windows and Linux
"""
import os
import sys
import time
import subprocess
from pathlib import Path

# Colors for terminal output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def strip():
        """Disable colors on Windows if not supported"""
        if sys.platform == 'win32' and not os.environ.get('ANSICON'):
            Colors.RED = Colors.GREEN = Colors.YELLOW = Colors.CYAN = Colors.NC = ''

Colors.strip()

def print_color(text, color=Colors.NC):
    print(f"{color}{text}{Colors.NC}")

def main():
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    pid_file = project_root / ".host_server.pid"
    
    print_color("=" * 50, Colors.CYAN)
    print_color("ArkNet Host Server Shutdown", Colors.CYAN)
    print_color("=" * 50, Colors.CYAN)
    
    # Check if PID file exists
    if not pid_file.exists():
        print_color("⚠️  No PID file found", Colors.YELLOW)
        print_color("   Host Server may not be running", Colors.YELLOW)
        sys.exit(0)
    
    # Read PID
    pid = int(pid_file.read_text().strip())
    
    # Check if process is running
    try:
        if sys.platform == 'win32':
            # Windows: check process using tasklist
            result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                  capture_output=True, text=True)
            is_running = str(pid) in result.stdout
        else:
            # Linux: send signal 0 to check if process exists
            os.kill(pid, 0)
            is_running = True
    except (OSError, ProcessLookupError):
        is_running = False
    
    if not is_running:
        print_color(f"⚠️  Process not found (PID: {pid})", Colors.YELLOW)
        print_color("   Removing stale PID file", Colors.YELLOW)
        pid_file.unlink()
        sys.exit(0)
    
    # Stop Host Server
    print_color(f"⏹️  Stopping Host Server (PID: {pid})...", Colors.YELLOW)
    
    try:
        if sys.platform == 'win32':
            # Windows: use taskkill
            subprocess.run(['taskkill', '/PID', str(pid), '/T', '/F'], 
                          check=True, capture_output=True)
        else:
            # Linux: send SIGTERM
            os.kill(pid, 15)  # SIGTERM
            
            # Wait for shutdown
            timeout = 15
            elapsed = 0
            while elapsed < timeout:
                try:
                    os.kill(pid, 0)  # Check if still running
                    time.sleep(1)
                    elapsed += 1
                    print(".", end="", flush=True)
                except OSError:
                    # Process terminated
                    break
            
            print()
            
            # Force kill if still running
            try:
                os.kill(pid, 0)
                print_color("⚠️  Graceful shutdown failed, forcing...", Colors.RED)
                os.kill(pid, 9)  # SIGKILL
                time.sleep(1)
            except OSError:
                pass
        
        # Verify stopped
        try:
            if sys.platform == 'win32':
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'], 
                                      capture_output=True, text=True)
                is_still_running = str(pid) in result.stdout
            else:
                os.kill(pid, 0)
                is_still_running = True
        except (OSError, ProcessLookupError):
            is_still_running = False
        
        if is_still_running:
            print_color("❌ Failed to stop Host Server", Colors.RED)
            sys.exit(1)
        else:
            print_color("✅ Host Server stopped successfully", Colors.GREEN)
            pid_file.unlink(missing_ok=True)
            
    except Exception as e:
        print_color(f"❌ Error stopping process: {e}", Colors.RED)
        sys.exit(1)
    
    print_color("=" * 50, Colors.CYAN)

if __name__ == "__main__":
    main()
