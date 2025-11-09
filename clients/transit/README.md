# clients/transit

TransitDataProvider — lightweight TypeScript package that provides REST + WebSocket adapters for route metadata and live vehicle positions.

Quick start (requires Node 18+ and npm):

1. Install deps

```powershell
cd clients/transit
npm ci
```

2. Build

```powershell
npx tsc --noEmit
```

3. Start mock server (for frontend dev)

```powershell
npm run start:mock
```

The package exposes a `TransitDataProvider` class (in `src/TransitDataProvider.ts`) and a mock server under `mock-server/`.
