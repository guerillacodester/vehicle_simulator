# Fleet Manager User Manual

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Installation & Setup](#installation--setup)
4. [API Reference](#api-reference)
5. [Database Configuration](#database-configuration)
6. [WebSocket Communication](#websocket-communication)
7. [Frontend Integration](#frontend-integration)
8. [Deployment Guide](#deployment-guide)
9. [Troubleshooting](#troubleshooting)
10. [Advanced Configuration](#advanced-configuration)

---

## Overview

The Fleet Manager is a comprehensive FastAPI-based system designed to manage vehicle fleets in real-time. It provides RESTful APIs, WebSocket communication for live telemetry, and database integration for persistent storage of vehicle data, routes, schedules, and operational metrics.

### Key Features

- **Real-time Vehicle Tracking** - Live GPS telemetry via WebSocket
- **Fleet Management** - Vehicle registration, status monitoring, route assignment
- **Database Integration** - PostgreSQL with SSH tunneling support
- **API-First Design** - RESTful endpoints for all operations
- **Socket.io Support** - Real-time bidirectional communication
- **Scalable Architecture** - Modular design with dependency injection

### System Requirements

- **Python 3.8+**
- **PostgreSQL 12+** (local or remote with SSH access)
- **FastAPI 0.104+**
- **Socket.io support**
- **SSH client** (for remote database connections)

---

## System Architecture

### Core Components

```text
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   Fleet Manager  │◄──►│   Database      │
│   (Next.js)     │    │   FastAPI API    │    │   PostgreSQL    │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • Dashboard     │    │ • REST Endpoints │    │ • Vehicle Data  │
│ • Live Maps     │    │ • Socket.io      │    │ • Routes        │
│ • Fleet Control│    │ • Authentication │    │ • Schedules     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │  Vehicle Devices │
                    │  GPS Telemetry   │
                    └──────────────────┘
```

### Directory Structure

```text
world/fleet_manager/
├── api/
│   ├── start_fleet_manager.py    # Main application entry point
│   ├── dependencies.py           # Database and auth dependencies
│   ├── routers/                  # API route handlers
│   │   ├── vehicles.py
│   │   ├── routes.py
│   │   ├── telemetry.py
│   │   └── fleet.py
│   └── schemas/                  # Pydantic data models
│       ├── vehicle.py
│       ├── route.py
│       └── telemetry.py
├── frontend/                     # Next.js web application
├── models/                       # Database ORM models
├── services/                     # Business logic services
└── docs/                         # Documentation
```

---

## Installation & Setup

### Prerequisites

1. **Python Environment**

   ```bash
   python --version  # Ensure Python 3.8+
   pip install --upgrade pip
   ```

2. **Install Dependencies**

   ```bash
   cd e:\projects\arknettransit\arknet_transit_simulator
   pip install -r requirements.txt
   ```

3. **Database Setup**

   Ensure PostgreSQL is available either:
   - Locally installed
   - Remote server with SSH access
   - Docker container

### Environment Configuration

Create `.env` file in the project root:

```env
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=fleet_user
DB_PASSWORD=secure_password
DB_NAME=fleet_manager

# SSH Tunnel (for remote database)
SSH_HOST=your-server.com
SSH_PORT=22
SSH_USER=your_ssh_user
SSH_KEY_PATH=/path/to/ssh/key

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
SECRET_KEY=your-secret-key-here
DEBUG=true

# Authentication
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_HOURS=24
```

### Quick Start

1. **Start the Fleet Manager API**

   ```bash
   python world\fleet_manager\api\start_fleet_manager.py
   ```

2. **Verify Installation**

   - API Health Check: `http://localhost:8000/health`
   - API Documentation: `http://localhost:8000/docs`
   - Socket.io Status: `http://localhost:8000/socket.io/`

3. **Frontend Development** (Optional)

   ```bash
   cd world\fleet_manager\frontend
   npm install
   npm run dev
   ```

---

## API Reference

### Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

### Authentication

Most endpoints require authentication via JWT tokens:

```http
Authorization: Bearer <your-jwt-token>
```

### Core Endpoints

#### Health & Status

- **GET** `/health` - API health check
- **GET** `/status` - System status and metrics

#### Vehicle Management

- **GET** `/api/v1/vehicles` - List all vehicles
- **POST** `/api/v1/vehicles` - Register new vehicle
- **GET** `/api/v1/vehicles/{vehicle_id}` - Get vehicle details
- **PUT** `/api/v1/vehicles/{vehicle_id}` - Update vehicle
- **DELETE** `/api/v1/vehicles/{vehicle_id}` - Remove vehicle

#### Route Management

- **GET** `/api/v1/routes` - List all routes
- **POST** `/api/v1/routes` - Create new route
- **GET** `/api/v1/routes/{route_id}` - Get route details
- **PUT** `/api/v1/routes/{route_id}` - Update route
- **DELETE** `/api/v1/routes/{route_id}` - Delete route

#### Fleet Operations

- **GET** `/api/v1/fleet/status` - Overall fleet status
- **POST** `/api/v1/fleet/dispatch` - Dispatch vehicle to route
- **PUT** `/api/v1/fleet/recall/{vehicle_id}` - Recall vehicle
- **GET** `/api/v1/fleet/metrics` - Fleet performance metrics

#### Telemetry

- **GET** `/api/v1/telemetry/live/{vehicle_id}` - Live vehicle data
- **GET** `/api/v1/telemetry/history/{vehicle_id}` - Historical data
- **POST** `/api/v1/telemetry/batch` - Bulk telemetry upload

### Request/Response Examples

#### Register Vehicle

**Request:**

```http
POST /api/v1/vehicles
Content-Type: application/json

{
    "vehicle_id": "BUS001",
    "registration": "ABC-123",
    "type": "bus",
    "capacity": 50,
    "status": "available",
    "depot_id": "DEPOT_01"
}
```

**Response:**

```json
{
    "success": true,
    "data": {
        "vehicle_id": "BUS001",
        "registration": "ABC-123",
        "type": "bus",
        "capacity": 50,
        "status": "available",
        "depot_id": "DEPOT_01",
        "created_at": "2025-09-09T20:00:00Z",
        "updated_at": "2025-09-09T20:00:00Z"
    }
}
```

#### Get Fleet Status

**Request:**

```http
GET /api/v1/fleet/status
Authorization: Bearer eyJ0eXAiOiJKV1Q...
```

**Response:**

```json
{
    "success": true,
    "data": {
        "total_vehicles": 25,
        "active_vehicles": 18,
        "available_vehicles": 7,
        "maintenance_vehicles": 0,
        "active_routes": 12,
        "last_update": "2025-09-09T20:00:00Z"
    }
}
```

---

## Database Configuration

### Schema Overview

The Fleet Manager uses PostgreSQL with the following key tables:

- **vehicles** - Vehicle registry and current status
- **routes** - Route definitions and schedules
- **telemetry** - GPS and sensor data
- **drivers** - Driver information and assignments
- **depots** - Vehicle storage and maintenance locations

### Connection Methods

#### Local Database

```python
# In dependencies.py
DATABASE_URL = "postgresql://user:password@localhost:5432/fleet_manager"
```

#### Remote Database with SSH Tunnel

```python
# Automatic SSH tunnel creation
ssh_tunnel = create_ssh_tunnel(
    ssh_host="your-server.com",
    ssh_port=22,
    ssh_user="your_user",
    remote_host="localhost",
    remote_port=5432,
    local_port=5433
)
DATABASE_URL = "postgresql://user:password@localhost:5433/fleet_manager"
```

### Database Migrations

Run migrations to set up the database schema:

```bash
# Using Alembic (if configured)
alembic upgrade head

# Or manual SQL scripts
psql -h localhost -U fleet_user -d fleet_manager -f schema.sql
```

### Performance Optimization

#### Indexes

Ensure proper indexing for high-performance queries:

```sql
-- Vehicle lookups
CREATE INDEX idx_vehicles_status ON vehicles(status);
CREATE INDEX idx_vehicles_route ON vehicles(current_route_id);

-- Telemetry queries
CREATE INDEX idx_telemetry_vehicle_time ON telemetry(vehicle_id, timestamp);
CREATE INDEX idx_telemetry_location ON telemetry USING GIST(location);

-- Route optimization
CREATE INDEX idx_routes_active ON routes(active) WHERE active = true;
```

#### Connection Pooling

Configure connection pooling for production:

```python
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)
```

---

## WebSocket Communication

### Socket.io Integration

The Fleet Manager provides real-time communication via Socket.io for:

- Live vehicle tracking
- Fleet status updates
- Alert notifications
- Driver communications

#### Connection

```javascript
// Frontend connection
import io from 'socket.io-client';

const socket = io('http://localhost:8000', {
    auth: {
        token: 'your-jwt-token'
    }
});
```

#### Event Handlers

**Server Events (Outgoing):**

```python
# In telemetry handler
await sio.emit('vehicle_update', {
    'vehicle_id': 'BUS001',
    'lat': 13.2810,
    'lon': -59.6463,
    'speed': 45.0,
    'timestamp': '2025-09-09T20:00:00Z'
}, room=f'vehicle_{vehicle_id}')
```

**Client Events (Incoming):**

```javascript
// Subscribe to vehicle updates
socket.emit('subscribe_vehicle', { vehicle_id: 'BUS001' });

// Handle real-time updates
socket.on('vehicle_update', (data) => {
    updateVehiclePosition(data);
});

// Handle fleet alerts
socket.on('fleet_alert', (alert) => {
    displayNotification(alert);
});
```

#### Room Management

Clients can join specific rooms for targeted updates:

```python
# Server-side room management
@sio.event
async def subscribe_vehicle(sid, data):
    vehicle_id = data['vehicle_id']
    await sio.enter_room(sid, f'vehicle_{vehicle_id}')
    await sio.emit('subscribed', {'vehicle_id': vehicle_id}, room=sid)
```

---

## Frontend Integration

### Next.js Application

The Fleet Manager includes a comprehensive Next.js frontend located in `world/fleet_manager/frontend/`.

#### Frontend Features

- **Real-time Dashboard** - Live fleet overview
- **Interactive Maps** - Vehicle tracking with route visualization
- **Fleet Management** - Vehicle and route administration
- **Analytics** - Performance metrics and reporting

#### Development Setup

```bash
cd world/fleet_manager/frontend

# Install dependencies
npm install

# Development server
npm run dev

# Production build
npm run build
npm start
```

#### Environment Variables

Frontend `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SOCKET_URL=http://localhost:8000
NEXT_PUBLIC_MAP_API_KEY=your_map_api_key
```

#### API Integration

```javascript
// API client setup
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export const fleetAPI = {
    async getVehicles() {
        const response = await fetch(`${API_BASE}/api/v1/vehicles`);
        return response.json();
    },
    
    async updateVehicle(vehicleId, data) {
        const response = await fetch(`${API_BASE}/api/v1/vehicles/${vehicleId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    }
};
```

---

## Deployment Guide

### Production Deployment

#### Using Docker

1. **Create Dockerfile**

   ```dockerfile
   FROM python:3.9-slim
   
   WORKDIR /app
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   
   COPY . .
   EXPOSE 8000
   
   CMD ["python", "world/fleet_manager/api/start_fleet_manager.py"]
   ```

2. **Docker Compose**

   ```yaml
   version: '3.8'
   services:
     fleet-manager:
       build: .
       ports:
         - "8000:8000"
       environment:
         - DB_HOST=postgres
         - DB_USER=fleet_user
         - DB_PASSWORD=secure_password
       depends_on:
         - postgres
   
     postgres:
       image: postgres:13
       environment:
         - POSTGRES_DB=fleet_manager
         - POSTGRES_USER=fleet_user
         - POSTGRES_PASSWORD=secure_password
       volumes:
         - postgres_data:/var/lib/postgresql/data
   
   volumes:
     postgres_data:
   ```

#### Using systemd (Linux)

1. **Create service file** `/etc/systemd/system/fleet-manager.service`

   ```ini
   [Unit]
   Description=Fleet Manager API
   After=network.target
   
   [Service]
   Type=simple
   User=fleet
   WorkingDirectory=/opt/fleet-manager
   ExecStart=/opt/fleet-manager/venv/bin/python world/fleet_manager/api/start_fleet_manager.py
   Restart=always
   RestartSec=10
   
   [Install]
   WantedBy=multi-user.target
   ```

2. **Enable and start**

   ```bash
   sudo systemctl enable fleet-manager
   sudo systemctl start fleet-manager
   sudo systemctl status fleet-manager
   ```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    location /socket.io/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

## Troubleshooting

### Common Issues

#### Database Connection Failed

**Symptoms:**

- API returns 500 errors
- "Connection refused" in logs

**Solutions:**

1. **Check database status**

   ```bash
   # Local PostgreSQL
   sudo systemctl status postgresql
   
   # Docker
   docker ps | grep postgres
   ```

2. **Verify connection parameters**

   ```python
   # Test connection manually
   import psycopg2
   conn = psycopg2.connect(
       host="localhost",
       port=5432,
       user="fleet_user",
       password="password",
       database="fleet_manager"
   )
   ```

3. **SSH tunnel issues**

   ```bash
   # Test SSH connection
   ssh -L 5433:localhost:5432 user@remote-server
   
   # Check tunnel in code
   print(f"SSH tunnel active: {tunnel.is_active}")
   ```

#### Socket.io Connection Issues

**Symptoms:**

- Frontend can't connect to WebSocket
- Real-time updates not working

**Solutions:**

1. **Check CORS configuration**

   ```python
   # In start_fleet_manager.py
   sio = AsyncServer(
       cors_allowed_origins=["http://localhost:3000", "https://your-domain.com"]
   )
   ```

2. **Verify client configuration**

   ```javascript
   const socket = io('http://localhost:8000', {
       transports: ['websocket', 'polling']
   });
   ```

#### Performance Issues

**Symptoms:**

- Slow API responses
- High CPU/Memory usage

**Solutions:**

1. **Database query optimization**

   ```sql
   -- Add missing indexes
   EXPLAIN ANALYZE SELECT * FROM vehicles WHERE status = 'active';
   
   -- Optimize slow queries
   CREATE INDEX CONCURRENTLY idx_vehicles_status_route 
   ON vehicles(status, current_route_id);
   ```

2. **Connection pooling**

   ```python
   # Adjust pool settings
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=30,
       pool_timeout=30
   )
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# In start_fleet_manager.py
if __name__ == "__main__":
    uvicorn.run("start_fleet_manager:app", 
                host="0.0.0.0", 
                port=8000, 
                debug=True,
                reload=True)
```

### Health Monitoring

Implement health checks:

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": await check_database_connection(),
        "memory_usage": get_memory_usage(),
        "active_connections": get_active_connections()
    }
```

---

## Advanced Configuration

### Scaling Considerations

#### Horizontal Scaling

1. **Load Balancer Configuration**

   ```nginx
   upstream fleet_backend {
       server 127.0.0.1:8000;
       server 127.0.0.1:8001;
       server 127.0.0.1:8002;
   }
   
   server {
       location / {
           proxy_pass http://fleet_backend;
       }
   }
   ```

2. **Database Connection Pooling**

   ```python
   # Production pool settings
   engine = create_engine(
       DATABASE_URL,
       pool_size=20,
       max_overflow=50,
       pool_timeout=30,
       pool_recycle=3600
   )
   ```

#### Caching Strategy

```python
import redis
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis_client = redis.from_url("redis://localhost:6379")
    FastAPICache.init(RedisBackend(redis_client), prefix="fleet-cache")

@app.get("/api/v1/vehicles")
@cache(expire=60)  # Cache for 60 seconds
async def get_vehicles():
    return await fetch_vehicles_from_db()
```

### Security

#### API Security

```python
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["your-domain.com", "*.your-domain.com"]
)
```

#### Rate Limiting

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/vehicles")
@limiter.limit("100/minute")
async def get_vehicles(request: Request):
    return await fetch_vehicles()
```

### Monitoring & Logging

#### Structured Logging

```python
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    
    logger.info(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time=process_time
    )
    return response
```

#### Metrics Collection

```python
from prometheus_client import Counter, Histogram, generate_latest

REQUEST_COUNT = Counter('requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('request_duration_seconds', 'Request latency')

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

### Backup & Recovery

#### Database Backup

```bash
#!/bin/bash
# backup.sh
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U fleet_user fleet_manager > backup_${TIMESTAMP}.sql
aws s3 cp backup_${TIMESTAMP}.sql s3://your-backup-bucket/
```

#### Configuration Backup

```python
import json
from datetime import datetime

def backup_configuration():
    config = {
        "vehicles": await get_all_vehicles(),
        "routes": await get_all_routes(),
        "settings": await get_system_settings(),
        "timestamp": datetime.now().isoformat()
    }
    
    with open(f"config_backup_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(config, f, indent=2)
```

---

**For technical support or additional documentation, contact the development team or check the project repository.**
