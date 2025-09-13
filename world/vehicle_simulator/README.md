Clean Vehicle Simulator
=======================

Minimal runtime: Depot Manager + Dispatcher only. No legacy GPS engine, telemetry server, or simulation threads.

Features
--------

* Fetch vehicle, driver, and route assignments from Fleet Manager API
* Display friendly (human) identifiers only – no UUID exposure
* Attach full route geometry (GPS coordinate count evidence)
* Simple lifecycle: initialize → (optional run) → shutdown

Quick Start
-----------

Display current assignments:

```bash
python -m world.vehicle_simulator --mode display
```

Run depot orchestration for 60 seconds:

```bash
python -m world.vehicle_simulator --mode depot --duration 60
```

Enable debug logging:

```bash
python -m world.vehicle_simulator --mode display --debug
```

Custom API base URL:

```bash
python -m world.vehicle_simulator --mode display --api-url http://127.0.0.1:8000
```

Programmatic Usage
------------------

```python
import asyncio
from world.vehicle_simulator.simulator import CleanVehicleSimulator

async def main():
	sim = CleanVehicleSimulator(api_url="http://localhost:8000")
	if not await sim.initialize():
		raise SystemExit("Init failed")
	assignments = await sim.get_vehicle_assignments()
	for a in assignments:
		print(a.vehicle_reg_code, a.driver_name, a.route_name)
	await sim.shutdown()

asyncio.run(main())
```

Entry Points
------------

* Module: `python -m world.vehicle_simulator`
* Script: `./simulator` (wrapper launching the module)

Modes
-----

| Mode    | Description                                    |
|---------|------------------------------------------------|
| display | One-shot fetch + evidence print + shutdown     |
| depot   | Long-running (or timed) orchestrator lifecycle |

Output Guarantees
-----------------

* No internal UUIDs surfaced in logs or console output
* Each route fetch includes geometry coordinate count when available
* Fails fast if API unreachable (no fake data fallback)

Future Extensions (Not Implemented Here)
----------------------------------------

* Real-time telemetry ingestion
* Vehicle motion simulation
* Web dashboard / streaming updates

This README describes the clean, security-tightened runtime. Legacy files were removed.

