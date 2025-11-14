# Transit Client Package

## Overview

TransitDataProvider — lightweight TypeScript package that connects the **Next.js dashboard** to the **Strapi backend API**. Provides REST + WebSocket adapters for route metadata and live vehicle positions.

## Production Architecture

```
Next.js Dashboard (Port 3000) → Strapi API (Port 1337) → PostgreSQL/PostGIS
```

**This package connects to your real Strapi backend**, not a mock server.

## Quick Start

### 1. Start Strapi Backend

```powershell
cd arknet_fleet_manager/arknet-fleet-api
npm run develop
# Strapi runs on http://localhost:1337
```

### 2. Configure Environment Variables

In `arknet_fleet_manager/dashboard/.env.local`:
```env
NEXT_PUBLIC_STRAPI_URL=http://localhost:1337/api
NEXT_PUBLIC_WS_URL=ws://localhost:1337
```

### 3. Build Transit Client

```powershell
cd clients/transit
npm ci
npx tsc --noEmit
```

### 4. Start Dashboard

```powershell
cd arknet_fleet_manager/dashboard
npm run dev
# Dashboard connects to Strapi automatically

```powershell
npm run start:mock
```

The package exposes a `TransitDataProvider` class (in `src/TransitDataProvider.ts`) and a mock server under `mock-server/`.
