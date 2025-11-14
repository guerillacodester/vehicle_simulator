# Commuter Service Client

Remote client console for managing and monitoring the Commuter Service.

## Features

- **Remote Management**: Connect to local or remote commuter service instances
- **Real-time Streaming**: Subscribe to passenger events via WebSocket
- **Passenger Seeding**: Trigger seeding operations remotely
- **Data Analysis**: Query manifests, statistics, and visualizations
- **Multi-client Support**: Server handles multiple concurrent connections

## Quick Start

### 1. Start the Commuter Service

```powershell
python commuter_service/main.py
```

The service will start on `http://localhost:4000`

### 2. Run the Client Console

```powershell
python clients/commuter/client_console.py
```

### 3. Connect and Use

```
commuter> connect
✅ Connected successfully!
   HTTP API: http://localhost:4000
   WebSocket: ✅ Connected

commuter> subscribe 1
📡 Subscribed to Route 1 events

commuter> seed 1 monday 7-9
🌱 SEEDING PASSENGERS
...
✅ SEEDING COMPLETE
Total Created: 45
```

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `connect [url]` | Connect to service | `connect http://192.168.1.100:4000` |
| `disconnect` | Disconnect from service | `disconnect` |
| `manifest <route> [date]` | Get passenger manifest | `manifest 1 2024-11-04` |
| `barchart <route> [date]` | Get hourly distribution | `barchart 1` |
| `subscribe <route>` | Subscribe to real-time events | `subscribe 1` |
| `unsubscribe <route>` | Unsubscribe from events | `unsubscribe 1` |
| `seed <route> <day> <hours>` | Seed passengers | `seed 1 monday 7-9` |
| `stats` | Show connection statistics | `stats` |
| `help` | Show command help | `help` |
| `exit` | Exit console | `exit` |

## Remote Connection

Connect to a remote server:

```
commuter> connect http://192.168.1.100:4000
Connecting to Commuter Service at http://192.168.1.100:4000...
✅ Connected successfully!
```

## Real-time Event Streaming

Subscribe to passenger events and watch them stream in real-time:

```
commuter> subscribe 1
📡 Subscribed to Route 1 events
   Listening for passenger:spawned, passenger:boarded, passenger:alighted

commuter> seed 1 monday 7-9
🌱 SEEDING PASSENGERS
...
(Events stream in as passengers are created)
```

## Architecture

```
┌─────────────────┐         HTTP/WS          ┌──────────────────┐
│  Client Console │ ◄─────────────────────► │ Commuter Service │
│  (Remote)       │                          │  (Server)        │
└─────────────────┘                          └──────────────────┘
                                                      │
                                                      ▼
                                              ┌──────────────┐
                                              │    Strapi    │
                                              │  (Database)  │
                                              └──────────────┘
```

- **Client**: GUI-agnostic console (can run anywhere)
- **Server**: Handles seeding, queries, real-time events
- **Database**: Strapi stores passenger data

## API Integration

The client uses the `CommuterConnector` class which provides:

- HTTP REST API client (httpx)
- WebSocket client for real-time events
- Observable pattern for event handling
- Auto-reconnection support

## Multi-Client Support

The server supports multiple concurrent clients:

- Each client maintains its own WebSocket connection
- Clients can subscribe to different routes
- Events are broadcast only to subscribed clients
- Thread-safe connection management

## Development

To extend the client:

1. Edit `clients/commuter/connector.py` for new API methods
2. Edit `clients/commuter/client_console.py` for new commands
3. Update command parser in `execute_command()`

Example adding a new command:

```python
elif cmd == "mycommand":
    await self.cmd_mycommand(args)

async def cmd_mycommand(self, args):
    """My custom command"""
    result = await self.connector.my_new_api_call()
    print(result)
```
