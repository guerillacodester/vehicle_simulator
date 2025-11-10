# ArkNet Transit Launcher — Design & Integration

This document captures the launcher design, goals, layout, and next steps. It's intended to complement `CONTEXT.md` and the project `TODO.md` by providing the authoritative plan for the production-grade launcher.

Overview
--------
The ArkNet Transit Launcher (internal name: `arknet-transit-launcher`) is the single authoritative entrypoint for starting, stopping, and managing runtime services used by the ArkNet Fleet System. It exposes a REST + WebSocket API consumed by the Next.js dashboard and (optionally) an Electron desktop UI.

Goals
-----
- Offer a single production-grade control plane for all services (Strapi, GPSCentCom, Geospatial, Redis, Next.js, simulators).
- Use OS-native service primitives where available (systemd, Windows Services, launchd) and fall back to per-user autostart when system-level control is not available.
- Forward logs to the OS logging stack (journald on Linux, Windows Event Log) and preserve rotating file logs for forensics.
- Provide extensible OS adapters and safe defaults so developer workflows remain frictionless (per-user autostart by default, system-wide only via installer/explicit opt-in).

Repository layout (planned)
---------------------------
```
arknet-transit-launcher/
├── arknet_transit_launcher/
│   ├── server.py                   # FastAPI app factory
│   ├── service_manager.py          # ManagedService lifecycle + API
│   ├── config.py                   # config schema & parser
│   ├── health.py                   # redis_probe, tcp checks
│   ├── process_launcher.py         # cross-platform process spawn & capture
│   ├── os_adapters/                # systemd / windows / launchd helpers
│   └── logging_adapters/           # journald / eventlog / file handlers
├── ui/
│   └── electron/                   # Electron tray app (primary user entrypoint)
└── packaging/                      # installer templates & systemd unit templates
```

Key design decisions
--------------------
- The launcher is authoritative; UI clients should never assume a service is present unless the launcher reports it available via `/services`.
- Autostart defaults to `process` (developer-friendly). `auto_start=system_service` requires explicit opt-in and is preferred if a system service is detected.
- Per-user autostart is the safe fallback (no elevation required) and will be the default for packaged developer installs.
- System-level registration of services (so they run pre-login) must be performed by the installer or an explicit privileged script; the launcher will provide helpers and templates but will not perform silent privileged operations.

APIs exposed (high-level)
-------------------------
- `GET /services` — list registered services and runtime metadata
- `GET /services/{name}/status` — status + detection fields (listening, installed, is_system_service, autostart_enabled)
- `POST /services/{name}/start` — start service (behavior depends on `auto_start` setting and adapters)
- `POST /services/{name}/stop` — stop service
- `POST /services/{name}/register-autostart` — create per-user autostart entry (explicit opt-in)
- `WS /events` — real-time service events

Next steps (implementation)
---------------------------
1. Scaffold `arknet-transit-launcher/` in repo root and add minimal FastAPI stub and config example.
2. Implement OS adapters (`systemd`, `windows_service`, `launchd`) that expose a consistent interface and are unit-tested (mocked subprocess calls).
3. Wire `auto_start` handling in `service_manager.py` so `POST /services/{name}/start` will prefer native service control when configured.
4. Add logging adapters and stream managed service stdout/stderr into OS logs.
5. Scaffold Electron UI that ensures the launcher server is running and provides tray/taskbar controls.

Contact
-------
For questions about the launcher design, see `TODO.md` for the prioritized plan or ask me to scaffold the project now.
