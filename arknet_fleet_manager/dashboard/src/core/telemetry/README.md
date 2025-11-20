# useTelemetry Hook

A custom React hook for consuming real-time vehicle telemetry data from the TelemetryProvider context. Provides live updates, connection state, diagnostics, and error handling for dashboard and UI components.

## API
```typescript
const { vehicles, connectionState, diagnostics, connectionType, error } = useTelemetry();
```

- **vehicles**: Array of vehicle telemetry objects (deviceId, lat, lon, speed, heading, route, driverName, timestamps, etc.)
- **connectionState**: 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error'
- **connectionType**: 'websocket' | 'sse'
- **diagnostics**: { state, connectionType, reconnectAttempts, wsFailures, useSSE, vehicleCount }
- **error**: Error object or undefined

## Usage Example
```tsx
import { useTelemetry } from './useTelemetry';

function VehicleDashboard() {
  const { vehicles, connectionState, diagnostics } = useTelemetry();

  return (
    <div>
      <h2>Connection: {connectionState}</h2>
      <pre>{JSON.stringify(diagnostics, null, 2)}</pre>
      <ul>
        {vehicles.map(v => (
          <li key={v.deviceId}>
            {v.deviceId}: {v.lat}, {v.lon} (Speed: {v.speed} km/h)
          </li>
        ))}
      </ul>
    </div>
  );
}
```

## Requirements
- Must be used inside a `<TelemetryProvider>`
- Handles WebSocket/SSE fallback, reconnection, and diagnostics automatically

## See Also
- `TelemetryProvider` (context)
- `TelemetryDataProvider` (core logic)
- Demo: `TelemetryWallDemo.tsx`, `TelemetryHookDemo.tsx`
