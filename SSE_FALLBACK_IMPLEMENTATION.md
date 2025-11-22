# SSE Fallback Implementation for Real-Time Telemetry

## Overview
Implemented Server-Sent Events (SSE) as a fallback mechanism for the dashboard's real-time vehicle telemetry when WebSocket connections fail or are unavailable.

## Implementation Summary

### Server-Side (GPSCentCom)
**File:** `gpscentcom_server/client_router.py`

- **SSE Endpoint:** `/sse`
- **Authentication:** Token via query parameter (`?token=...`) or Bearer header
- **Protocol:** Standard SSE format (`data: {...}\n\n`)
- **Topic:** Subscribes to `telemetry` topic via broker
- **Cleanup:** Automatic unsubscribe on client disconnect

**Test Client:** `test_sse_client.py` - Python script to validate SSE endpoint

### Client-Side (TypeScript Dashboard)
**File:** `arknet_fleet_manager/dashboard/src/core/telemetry/TelemetryDataProvider.ts`

#### Connection Strategy
1. **Primary:** Attempt WebSocket connection first
2. **Fallback Trigger:** After 3 consecutive WebSocket failures, switch to SSE
3. **Background Retry:** Continue attempting WebSocket reconnection every 60s while using SSE
4. **Automatic Switch:** When WebSocket succeeds, automatically switch back from SSE

#### Key Features
- **Dual Protocol Support:** WebSocket and SSE in single provider
- **Transparent Fallback:** No changes required to consumer code
- **Connection Diagnostics:** Expose connection type and failure metrics
- **Infinite Reconnects:** Both protocols retry indefinitely
- **Graceful Degradation:** Seamless transition between protocols

#### New API Methods
```typescript
getConnectionType(): TelemetryConnectionType  // Returns 'websocket' or 'sse'
getDiagnostics(): {
  state: TelemetryConnectionState,
  connectionType: TelemetryConnectionType,
  reconnectAttempts: number,
  wsFailures: number,
  useSSE: boolean,
  vehicleCount: number
}
```

## Testing

### Server-Side SSE Test
```bash
python test_sse_client.py http://localhost:5000/sse?token=supersecrettoken
```

**Expected Output:**
```
Connected to SSE endpoint. Waiting for events...
Event: {'type': 'update', 'deviceId': 'GPS-ZR102', ...}
Event: {'type': 'update', 'deviceId': 'GPS-ZR102', ...}
```

### Client-Side Integration
The TelemetryDataProvider automatically handles fallback:

```typescript
const provider = new TelemetryDataProvider('http://localhost:5000', 'supersecrettoken');
provider.connect();

// Monitor connection type
provider.onStatus((state) => {
  const diagnostics = provider.getDiagnostics();
  console.log(`Connection: ${diagnostics.connectionType} (${diagnostics.state})`);
});

// Subscribe to vehicle updates (works with both WebSocket and SSE)
provider.subscribe((vehicles) => {
  console.log(`Received ${vehicles.length} vehicles`);
});
```

## Benefits

1. **Reliability:** Continues operation even when WebSocket is blocked/unavailable
2. **Firewall Friendly:** SSE uses standard HTTP, better compatibility with restrictive networks
3. **Automatic Recovery:** Switches back to WebSocket when available
4. **Zero Configuration:** Fallback happens automatically based on connection health
5. **Production Ready:** Robust error handling and infinite retry logic

## Network Compatibility

- **WebSocket:** Low latency, bidirectional, but may be blocked by firewalls/proxies
- **SSE:** HTTP-based, better firewall compatibility, server-to-client only
- **Automatic Selection:** Client automatically uses best available protocol

## DevOps Integration

This implementation supports the **Real-Time Telemetry Redundancy** feature in Iteration 3:
- **Story AB#4281 - Task 1:** SSE endpoint implementation ✅
- **Story AB#4281 - Task 2:** Client-side fallback logic ✅
- **Story AB#4281 - Task 3:** Connection diagnostics and monitoring ✅

## Future Enhancements

1. **Connection Preference:** Allow manual override to force WebSocket or SSE
2. **Metrics Collection:** Track fallback frequency and connection quality
3. **Health Reporting:** Report connection type to backend for analytics
4. **Long Polling Fallback:** Add long polling as third fallback option
