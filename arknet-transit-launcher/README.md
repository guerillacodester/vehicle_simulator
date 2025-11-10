# ArkNet Transit Launcher

Production-grade launcher for ArkNet services (Strapi, NextJS dashboard, Redis, simulators).

This repo contains the `arknet-transit-launcher` — a FastAPI-based service manager, OS adapters to control native system services (systemd / Windows Service / launchd), logging adapters to forward logs to OS logging subsystems, and a cross-platform Electron desktop UI (tray) that acts as the primary user entrypoint.

See `docs/` for architecture and operational guides.
