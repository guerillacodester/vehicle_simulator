# ArkNet Transit Launcher

Production-grade launcher for ArkNet services (Strapi, NextJS dashboard, Redis, simulators).

This repo contains the `arknet-transit-launcher` — a FastAPI-based service manager, OS adapters to control native system services (systemd / Windows Service / launchd), logging adapters to forward logs to OS logging subsystems, and a cross-platform Electron desktop UI (tray) that acts as the primary user entrypoint.

See `docs/` for architecture and operational guides.

## API Endpoints

### Autostart Management

The launcher provides REST API endpoints for managing per-user autostart settings.

#### POST /autostart/enable
Enable autostart for a service on user login.

**Request Body:**
```json
{
  "service": "string"
}
```

**Response:**
```json
{
  "message": "Autostart enabled for <service>"
}
```

**Permissions:** Requires `can_manage_autostart` (Dispatcher+) or `can_manage_all_autostart` (Admin).

#### POST /autostart/disable
Disable autostart for a service.

**Request Body:**
```json
{
  "service": "string"
}
```

**Response:**
```json
{
  "message": "Autostart disabled for <service>"
}
```

**Permissions:** Same as enable.

#### GET /autostart/status
Check if autostart is enabled for a service.

**Query Parameters:**
- `service`: string

**Response:**
```json
{
  "service": "string",
  "autostart_enabled": true
}
```

**Permissions:** Requires `can_view_services` (Dispatcher+).

### Usage
- Linux: Uses `systemctl --user` for systemd user units.
- Windows: Uses `schtasks` for Task Scheduler on logon.
- Ensure the launcher runs with appropriate permissions for OS interactions.
