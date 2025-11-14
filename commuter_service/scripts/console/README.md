# Console Passenger Tools

Minimal, production-friendly console tools for viewing historic and realtime passenger spawns.

## Historic - list_passengers.py
Lists rows from Strapi `active-passengers` with filters and multiple output modes.

Env:
- STRAPI_URL (default <http://localhost:1337>)
- STRAPI_TOKEN (optional)

Examples:
```powershell
# By route and time window
python -m commuter_service.scripts.console.list_passengers --route gg3pv3z19hhm117v9xth5ezq --start 2025-10-29T09:00:00Z --end 2025-10-29T10:00:00Z

# By depot
python -m commuter_service.scripts.console.list_passengers --depot abcd1234 --limit 50

# Recent only (table) and JSON modes
python -m commuter_service.scripts.console.list_passengers --limit 10 --sort createdAt:desc
python -m commuter_service.scripts.console.list_passengers --route gg3pv3z19hhm117v9xth5ezq --json | jq '.'
```

## Realtime - stream_passenger_events.py
Streams Postgres NOTIFY events on channel `active_passengers` (decoupled from Strapi/Geo) and prints pretty or NDJSON.

Env:
- PG_DSN (postgresql://user:password@host:5432/dbname)

Examples:
```powershell
# Start stream
$env:PG_DSN = "postgresql://<user>:<password>@<host>:5432/<database>"
python -m commuter_service.scripts.console.stream_passenger_events

# Filter by route and output NDJSON
python -m commuter_service.scripts.console.stream_passenger_events --route gg3pv3z19hhm117v9xth5ezq --json | jq '.'
```

## Postgres Trigger (LISTEN/NOTIFY)
To emit events on inserts/updates to `active_passengers`, run:
- `commuter_service/scripts/sql/active_passengers_notify.sql`

Adjust table/column names for your Strapi schema if needed.

## Tips
- You can combine these with the spawner harness to validate realism quickly.
- NDJSON output makes it easy to pipe to `jq`, `rg`, or log shippers.
