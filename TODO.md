# ArkNet Fleet Manager — Master TODO

This file is the single source for prioritized work across backend, launcher, and frontend. It mirrors the project plan and explicit steps required to make `arknet-transit-launcher` (the production launcher), the Next.js dashboard, and backend services production-ready.

Last updated: November 10, 2025

## Top-level priorities (short-term)

1. Stability & Logging (DONE)
	- Prevent logging from throwing (safe stringification, fallback transports)
	- Forward service stdout/stderr safely to OS logging or rotating file when OS handlers unavailable

2. Redis resiliency & detection (DONE)
	- Harden ioredis clients with retry/backoff and rate-limited error logs
	- Add `redis_probe` (TCP + PATH + system-service checks) and expose via `/services` status

3. Launcher health-probe and UI hardening (DONE)
	- Dashboard probes launcher `/health` before attempting Socket.IO
	- Removed stale compiled artifacts that caused mismatches

## Core work items (this sprint)

4. OS-native service adapters (IN PROGRESS)
	- Implement `systemd` adapter (system + user) with detect/start/stop/enable/disable
	- Implement Windows service adapter using `sc` / PowerShell and per-user Startup folder helper
	- Expose capability via `launcher/os_adapters` and unit tests (mocked)

5. Auto-start wiring into launcher (next)
	- Add `auto_start` config: none | process | system_service | user_service
	- Respect `auto_start` when POST /services/{name}/start — prefer OS adapter when configured
	- Provide explicit endpoint POST /services/{name}/register-autostart for user-service registration

6. Per-user autostart fallback (safe default)
	- Linux: `systemd --user` unit creation and `systemctl --user enable --now`
	- Windows: create Startup folder shortcut or per-user Run registry key
	- macOS: LaunchAgents plist in `~/Library/LaunchAgents`

7. OS-native logging adapters
	- journald adapter for Linux (use systemd-journal bindings if available)
	- Windows Event Log adapter (pywin32 optional) or fallback file logging
	- Capture and forward service stdout/stderr into these adapters with service tags

8. Add Next.js (dashboard) as a managed service
	- Add `dashboard`/`nextjs` to `launcher/config.py` parsing and ServiceFactory
	- Start/stop via `npm run dev` (dev) or `npm run build && npm run start` (prod)

## Productization (mid-term)

9. Desktop UI (Electron) — primary entrypoint
	- Electron tray app ensures launcher server is running, provides Start/Stop, and opens dashboard
	- Single-instance, auto-update-friendly packaging

10. Packaging & installers
	 - Create installers that register system-level services and enable autostart (deb/rpm, MSI/NSIS, pkg/dmg)
	 - Installer should be the recommended way to get system services running pre-login

11. Tests, CI & release pipelines
	 - Unit tests for probes and os adapters, integration smoke tests (mocked), CI matrix (Windows/Linux/macOS)

12. Docs & runbooks
	 - `docs/ARCHITECTURE.md`, `docs/OPERATIONS.md`, `examples/config.example.ini`

## Full task list (detailed)
- See `CONTEXT.md` for architecture and component responsibilities
- See `arknet-transit-launcher/README.md` (scaffold to be created) for launcher-specific run instructions

---

If you want, I can now:
- Scaffold the `arknet-transit-launcher/` folder and starter files, or
- Implement the `systemd` and `windows_service` adapters and wire `auto_start` handling into the launcher API.

Pick one and I'll proceed.
