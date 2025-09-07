#!/usr/bin/env python
# This file can be run directly on Windows with proper Python file association

if __name__ == "__main__":
    import subprocess
    import sys
    import os
    
    # Get the directory containing this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    main_py = os.path.join(script_dir, "main.py")
    
    # Use py launcher to run main.py
    try:
        subprocess.run(["py", main_py] + sys.argv[1:])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except FileNotFoundError:
        print("❌ Python launcher 'py' not found. Try: python main.py")
    except Exception as e:
        print(f"❌ Error: {e}")
