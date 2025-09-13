#!/usr/bin/env python3
"""
Test script to demonstrate the interactive passenger modeler
"""
import subprocess
import sys
from pathlib import Path

def test_interactive():
    """Test the interactive mode"""
    print("Testing interactive passenger modeler...")
    
    # Change to the passenger_modeler directory
    modeler_dir = Path(__file__).parent
    
    # Test with simulated input:
    # - Press Enter for default (poisson)
    # - Enter "test_model" as output name
    test_input = "\ntest_model\n"
    
    try:
        result = subprocess.run(
            [sys.executable, "main.py"],
            input=test_input,
            text=True,
            capture_output=True,
            cwd=modeler_dir,
            timeout=30
        )
        
        print("STDOUT:")
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        print(f"Return code: {result.returncode}")
        
        # Check if output file was created
        output_file = modeler_dir / "models" / "generated" / "test_model.json"
        if output_file.exists():
            print(f"✅ Output file created: {output_file}")
            print(f"File size: {output_file.stat().st_size} bytes")
        else:
            print(f"❌ Output file not found: {output_file}")
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    test_interactive()