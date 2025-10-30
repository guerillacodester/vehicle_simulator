"""
Console process launcher for cross-platform service execution.

Single Responsibility: Launching services in separate console windows.
Open/Closed Principle: Extensible for different platforms.
"""

import sys
import subprocess
from pathlib import Path
from typing import Optional, List


class ConsoleLauncher:
    """
    Launches services in new console windows.
    
    Single Responsibility: Process creation and console management.
    """
    
    def launch(
        self,
        service_name: str,
        title: str,
        script_path: Optional[Path] = None,
        as_module: Optional[str] = None,
        is_npm: bool = False,
        npm_command: Optional[str] = None,
        extra_args: Optional[List[str]] = None
    ) -> Optional[subprocess.Popen]:
        """
        Launch a service in a new console window.
        
        Args:
            service_name: Name of the service (for error reporting)
            title: Console window title
            script_path: Path to script file (or npm project directory)
            as_module: Python module to run (e.g., 'arknet_transit_simulator')
            is_npm: True if this is an npm project
            npm_command: npm command to run (e.g., 'develop', 'start')
            extra_args: Additional command-line arguments
            
        Returns:
            Process handle or None if launch failed
        """
        if script_path and not script_path.exists():
            print(f"   ⚠️  {service_name}: {script_path} not found - SKIPPED")
            return None
        
        # Build command based on service type
        if is_npm:
            base_cmd, cwd = self._build_npm_command(script_path, npm_command)
        elif as_module:
            base_cmd, cwd = self._build_module_command(as_module, extra_args)
        else:
            base_cmd, cwd = self._build_script_command(script_path, extra_args)
        
        # Launch based on platform
        try:
            if sys.platform == "win32":
                return self._launch_windows(base_cmd, cwd, title)
            elif sys.platform == "darwin":
                return self._launch_macos(base_cmd, cwd, title)
            else:
                return self._launch_linux(base_cmd, cwd, title)
        except Exception as e:
            print(f"   ❌ Failed to launch {service_name}: {e}")
            return None
    
    def _build_npm_command(self, project_dir: Path, npm_command: Optional[str]):
        """Build npm command."""
        cmd = ['npm', 'run', npm_command] if npm_command else ['npm', 'start']
        return cmd, project_dir
    
    def _build_module_command(self, module: str, extra_args: Optional[List[str]]):
        """Build Python module command."""
        cmd = [sys.executable, '-m', module] + (extra_args or [])
        return cmd, Path.cwd()
    
    def _build_script_command(self, script_path: Path, extra_args: Optional[List[str]]):
        """Build Python script command."""
        cmd = [sys.executable, str(script_path)] + (extra_args or [])
        return cmd, script_path.parent
    
    def _launch_windows(self, cmd: List[str], cwd: Path, title: str) -> subprocess.Popen:
        """Launch on Windows - spawns new console window"""
        # Build command string with proper quoting for paths with spaces
        quoted_cmd = []
        for arg in cmd:
            arg_str = str(arg)
            # Quote arguments that contain spaces (like Python executable path)
            if ' ' in arg_str and not (arg_str.startswith('"') and arg_str.endswith('"')):
                quoted_cmd.append(f'"{arg_str}"')
            else:
                quoted_cmd.append(arg_str)
        
        cmd_str = ' '.join(quoted_cmd)
        
        # For npm commands on Windows, we need to use 'call npm' to ensure proper execution
        if cmd[0] == 'npm':
            cmd_str = f'call {cmd_str}'
        
        # Launch new console window
        return subprocess.Popen(
            [
                "cmd.exe",
                "/c",
                "start",
                title,
                "cmd.exe",
                "/k",
                f"cd /d {cwd} && {cmd_str} || pause"
            ],
            cwd=cwd
        )
            ],
            cwd=cwd
        )
    
    def _launch_macos(self, cmd: List[str], cwd: Path, title: str) -> subprocess.Popen:
        """Launch on macOS."""
        cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in cmd])
        applescript = f'''
            tell application "Terminal"
                do script "cd {cwd} && {cmd_str}"
                set custom title of front window to "{title}"
            end tell
        '''
        return subprocess.Popen(['osascript', '-e', applescript], cwd=cwd)
    
    def _launch_linux(self, cmd: List[str], cwd: Path, title: str) -> subprocess.Popen:
        """Launch on Linux (tries multiple terminal emulators)."""
        cmd_str = ' '.join([f'"{arg}"' if ' ' in arg else arg for arg in cmd])
        
        terminal_commands = [
            ['gnome-terminal', '--title', title, '--', 'bash', '-c', f'cd {cwd} && {cmd_str}; exec bash'],
            ['konsole', '--new-tab', '--title', title, '-e', 'bash', '-c', f'cd {cwd} && {cmd_str}; exec bash'],
            ['xterm', '-T', title, '-e', f'cd {cwd} && {cmd_str}; exec bash'],
            ['terminator', '-T', title, '-e', f'bash -c "cd {cwd} && {cmd_str}; exec bash"'],
            ['xfce4-terminal', '--title', title, '--command', f'bash -c "cd {cwd} && {cmd_str}; exec bash"'],
        ]
        
        for term_cmd in terminal_commands:
            try:
                process = subprocess.Popen(term_cmd, cwd=cwd)
                print(f"   ℹ️  Using terminal: {term_cmd[0]}")
                return process
            except FileNotFoundError:
                continue
        
        # No terminal found, run in background
        print(f"   ⚠️  No terminal emulator found - running in background")
        return subprocess.Popen(cmd, cwd=cwd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
