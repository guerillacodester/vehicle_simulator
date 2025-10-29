"""
Console - Realtime Passenger Stream
-----------------------------------

Listen to Postgres NOTIFY events on channel 'active_passengers' and print them to console.

Env:
- PG_DSN (e.g., postgresql://user:password@host:5432/dbname)

Usage:
    python -m commuter_simulator.scripts.console.stream_passenger_events [--route ROUTE_ID] [--depot DEPOT_ID] [--json]

Optional psql sanity check:
  psql "..." -c "NOTIFY active_passengers, '{""action"":""TEST"", ""latitude"":13.19, ""longitude"":-59.54}'"
"""

from __future__ import annotations

import os
import sys
import asyncio
import json
import logging
from typing import Any, Optional

import asyncpg
import argparse


CHANNEL = "active_passengers"
logger = logging.getLogger("stream_passenger_events")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


def pretty(ev: dict[str, Any]) -> str:
    def g(k: str, default: Any = None):
        return ev.get(k, default)
    lat = g("latitude", "-")
    lon = g("longitude", "-")
    action = g("action", "EVT")
    pid = g("passenger_id", "-")
    rid = g("route_id", "-")
    did = g("depot_id", "-")
    ts = g("spawned_at", "-")
    return f"{action:<6} {ts:<20} {pid:<16} route={rid:<24} depot={did:<12} lat={lat} lon={lon}"


async def main_async():
    parser = argparse.ArgumentParser(description="Stream passenger events from Postgres NOTIFY")
    parser.add_argument("--route", help="Filter by route_id", default=None)
    parser.add_argument("--depot", help="Filter by depot_id", default=None)
    parser.add_argument("--json", help="Output NDJSON instead of pretty lines", action="store_true")
    args = parser.parse_args()

    dsn = os.getenv("PG_DSN")
    if not dsn:
        logger.error("PG_DSN is not set")
        sys.exit(1)

    queue: asyncio.Queue[str] = asyncio.Queue(maxsize=10000)

    async def connect_and_listen():
        backoff = 1
        while True:
            try:
                conn = await asyncpg.connect(dsn, timeout=10)
                await conn.add_listener(CHANNEL, lambda *args: None)

                def _on_notify(connection, pid, channel, payload):
                    try:
                        queue.put_nowait(payload)
                    except asyncio.QueueFull:
                        try:
                            queue.get_nowait()
                            queue.put_nowait(payload)
                        except Exception:
                            pass

                await conn.remove_listener(CHANNEL, lambda *args: None)
                await conn.add_listener(CHANNEL, _on_notify)

                logger.info(f"Connected. Listening on channel '{CHANNEL}' (Ctrl+C to exit)")
                # Keepalive loop
                while True:
                    await asyncio.sleep(30)
                    try:
                        await conn.execute("SELECT 1")
                    except Exception as e:
                        logger.warning(f"Connection keepalive failed: {e}")
                        try:
                            await conn.close()
                        except Exception:
                            pass
                        break
                # Back to reconnect
            except Exception as e:
                logger.error(f"Listen connection error: {e}")
            # Exponential backoff up to 30s
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)

    async def consume_loop():
        while True:
            payload = await queue.get()
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                if args.json:
                    print(json.dumps({"raw": payload}), flush=True)
                else:
                    print(f"RAW: {payload}", flush=True)
                continue

            # Apply optional filters
            if args.route and data.get("route_id") != args.route:
                continue
            if args.depot and data.get("depot_id") != args.depot:
                continue

            if args.json:
                print(json.dumps(data), flush=True)
            else:
                print(pretty(data), flush=True)

    listener = asyncio.create_task(connect_and_listen())
    consumer = asyncio.create_task(consume_loop())
    try:
        await asyncio.gather(listener, consumer)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        for t in (listener, consumer):
            try:
                t.cancel()
            except Exception:
                pass


if __name__ == "__main__":
    asyncio.run(main_async())
