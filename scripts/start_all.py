#!/usr/bin/env python3
"""
ArkNet Host Server - Start All Services
Cross-platform startup script for Windows and Linux
"""
import os
import sys
import time
import signal
import subprocess
import argparse
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
    parser = argparse.ArgumentParser(description="Start ArkNet Host Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=6000, help="Port to bind to")
    args = parser.parse_args()
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    log_dir = project_root / "logs"
    pid_file = project_root / ".host_server.pid"
    
    # Use system Python directly (no venv required)
    python_exe = sys.executable
    
    print_color("=" * 50, Colors.CYAN)
    print_color("ArkNet Host Server Startup", Colors.CYAN)
    print_color("=" * 50, Colors.CYAN)
    
    # Check if already running
    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
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
        
        if is_running:
            print_color(f"⚠️  Host Server already running (PID: {pid})", Colors.YELLOW)
            print_color("   Use stop_all.py to stop it first", Colors.YELLOW)
            sys.exit(1)
        else:
            print_color("⚠️  Stale PID file found, removing...", Colors.YELLOW)
            pid_file.unlink()
    
    # Create log directory
    log_dir.mkdir(exist_ok=True)
    
    # Check dependencies
    print_color("🔍 Checking dependencies...", Colors.CYAN)
    try:
        subprocess.run([python_exe, "-c", "import fastapi, uvicorn, httpx"],
                      check=True, capture_output=True)
        print_color("✅ Dependencies OK", Colors.GREEN)
    except subprocess.CalledProcessError:
        print_color("⚠️  Missing dependencies, installing...", Colors.YELLOW)
        subprocess.run([python_exe, "-m", "pip", "install", "-q", "fastapi", "uvicorn", "httpx"],
                      check=True)
    
    # Start Host Server
    print_color("🚀 Starting Host Server...", Colors.CYAN)
    
    log_file = log_dir / "host_server.log"
    
    # Start subprocess
    with open(log_file, 'w') as log:
        if sys.platform == 'win32':
            # Windows: use CREATE_NEW_PROCESS_GROUP to detach
            process = subprocess.Popen(
                [python_exe, "-m", "services.host_server", 
                 "--host", args.host, "--port", str(args.port)],
                stdout=log,
                stderr=log,
                cwd=str(project_root),
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
        else:
            # Linux: use start_new_session
            process = subprocess.Popen(
                [python_exe, "-m", "services.host_server",
                 "--host", args.host, "--port", str(args.port)],
                stdout=log,
                stderr=log,
                cwd=str(project_root),
                start_new_session=True
            )
    
    # Save PID
    pid_file.write_text(str(process.pid))
    
    # Wait for startup
    print_color("⏳ Waiting for Host Server to start...", Colors.YELLOW)
    time.sleep(3)
    
    # Check if process is still running
    if process.poll() is None:
        print_color("✅ Host Server started successfully!", Colors.GREEN)
        print_color(f"   PID:     {process.pid}", Colors.GREEN)
        print_color(f"   URL:     http://localhost:{args.port}", Colors.GREEN)
        print_color(f"   Health:  http://localhost:{args.port}/health", Colors.GREEN)
        print_color(f"   Logs:    tail -f {log_file}", Colors.GREEN)
        print()
        print_color("📋 Next Steps:", Colors.CYAN)
        print_color("   1. Connect console:  python -m clients.fleet", Colors.CYAN)
        print_color("   2. Check services:   services", Colors.CYAN)
        print_color("   3. Start simulator:  start-service simulator", Colors.CYAN)
    else:
        print_color("❌ Failed to start Host Server", Colors.RED)
        print_color(f"   Check logs: {log_file}", Colors.RED)
        pid_file.unlink(missing_ok=True)
        sys.exit(1)
    
    print_color("=" * 50, Colors.CYAN)

if __name__ == "__main__":
    main()
