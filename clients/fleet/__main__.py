"""Fleet Management Console Entry Point"""

import asyncio
from .fleet_console import main

if __name__ == "__main__":
    asyncio.run(main())
