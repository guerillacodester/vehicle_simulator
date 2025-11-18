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

## Configuration

The launcher uses a `config.ini` file for service configuration. Copy `config.example.ini` to `config.ini` and modify as needed.

### Autostart Configuration

Services can be configured to start automatically using the `auto_start` setting:

```ini
[redis]
enabled = true
auto_start = user_service  # Options: process, system_service, user_service, none
register_autostart = true  # Set to true to register the autostart on first run
```

**auto_start options:**
- `process`: Start as a background process managed by the launcher
- `system_service`: Use OS system service (requires admin/root)
- `user_service`: Use OS user service (recommended for per-user autostart)
- `none`: Manual start only

**Example for Strapi:**
```ini
[strapi]
enabled = true
auto_start = user_service
register_autostart = true
port = 1337
```

**Note:** On first run with `register_autostart = true`, the launcher will attempt to register the service for autostart. This may require elevated permissions.
