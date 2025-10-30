# GPS Device Automatic Reconnection Implementation

**Date**: October 30, 2025  
**Component**: `arknet_transit_simulator/vehicle/gps_device/device.py`  
**Issue**: GPS devices not reconnecting after GPSCentCom server restart

## Problem Statement

When the GPSCentCom server goes down after vehicle simulators are running, the GPS devices would fail to reconnect when the server comes back online. This is critical for real hardware deployment where:

- Network interruptions are common
- Users don't have software access to know when devices lose connection
- Manual reconnection is not feasible for isolated hardware devices

## Root Cause

The original `_async_transmitter()` method:
1. Connected **once** at startup
2. If connection failed → entire transmitter worker exited
3. If connection dropped during transmission → worker exited
4. No retry or reconnection logic

```python
# OLD BEHAVIOR (BROKEN)
async def _async_transmitter(self):
    try:
        await self.transmitter.connect()  # ← Connect once
        while not self._stop.is_set():
            # ... send data ...
    except Exception as e:
        logger.error(f"Connection error: {e}")
        # ← Worker exits, never reconnects
```

## Solution: Resilient Connection Loop

Implemented a robust reconnection mechanism with:

### 1. **Automatic Reconnection**
- Continuously attempts to connect if server unavailable
- Reconnects automatically if connection drops
- Configurable retry delay (default: 5 seconds)

### 2. **Error Recovery**
- Handles connection failures gracefully
- Detects network errors during transmission
- Forces reconnection after consecutive errors (default: 3)

### 3. **Connection State Management**
- Tracks connection status (`connected` flag)
- Distinguishes between connection phase and transmission phase
- Clean disconnection on shutdown

### 4. **Specific Exception Handling**

| Exception Type | Behavior |
|----------------|----------|
| `ConnectionRefused` | Log warning, retry connection |
| `websockets.exceptions.ConnectionClosed` | Log warning, force reconnect |
| `OSError` / `ConnectionError` | Count errors, reconnect after threshold |
| `websockets.exceptions.WebSocketException` | Count errors, reconnect after threshold |
| `asyncio.TimeoutError` | Normal timeout, continue |
| Other exceptions | Log error, count, potentially reconnect |

## Implementation Details

```python
async def _async_transmitter(self):
    """
    Async worker with automatic reconnection.
    
    Features:
    - Attempts connection on startup
    - Reconnects if connection drops
    - Continues operating when server unavailable
    - Buffers data during disconnection (up to buffer capacity)
    """
    connection_retry_delay = 5.0  # Seconds between reconnection attempts
    max_consecutive_errors = 3    # Max errors before forcing reconnect
    connected = False
    consecutive_errors = 0
    
    while not self._stop.is_set():
        # CONNECTION PHASE
        if not connected:
            try:
                await self.transmitter.connect()
                connected = True
                consecutive_errors = 0
            except Exception as e:
                # Log error and retry after delay
                await asyncio.sleep(connection_retry_delay)
                continue
        
        # TRANSMISSION PHASE
        try:
            data = await asyncio.to_thread(self.rxtx_buffer.read, timeout=1.0)
            if data:
                await self.transmitter.send(data)
                consecutive_errors = 0  # Reset on success
                
        except websockets.exceptions.ConnectionClosed:
            # Connection dropped - force reconnect
            connected = False
            await self.transmitter.close()
            
        except (OSError, ConnectionError, websockets.exceptions.WebSocketException):
            # Network error - count and potentially reconnect
            consecutive_errors += 1
            if consecutive_errors >= max_consecutive_errors:
                connected = False
                await self.transmitter.close()
```

## Configuration Parameters

| Parameter | Default | Purpose |
|-----------|---------|---------|
| `connection_retry_delay` | 5.0 seconds | Delay between reconnection attempts |
| `max_consecutive_errors` | 3 | Errors before forcing reconnect |
| Buffer read timeout | 1.0 seconds | Timeout for reading from data buffer |

## Buffer Behavior During Disconnection

- **Data Collection**: Continues (plugin still generates telemetry)
- **Buffer Writing**: Continues (data worker still writes to buffer)
- **Buffer Capacity**: 1000 items (configured in RxTxBuffer)
- **Overflow Behavior**: Oldest data dropped (FIFO queue)
- **Transmission**: Resumes when connection restored

**Important**: Data is buffered during disconnection up to capacity. Long disconnections (>1000 updates) will result in data loss for oldest items.

## Testing

### Test Script
Use `test_gps_reconnection.py` to verify behavior:

```bash
# Terminal 1: Start test (GPS server not required)
python test_gps_reconnection.py

# Terminal 2: Start/stop GPS server to test reconnection
python gpscentcom_server/server_main.py
# Press Ctrl+C to stop
# Start again to test reconnection
```

### Expected Behavior

1. **Server Down on Startup**:
   ```
   📡 TEST-GPS-001: Attempting to connect to GPS server...
   📡 TEST-GPS-001: GPS server not available - will retry in 5s
   📡 TEST-GPS-001: Attempting to connect to GPS server...
   📡 TEST-GPS-001: GPS server not available - will retry in 5s
   ```

2. **Server Becomes Available**:
   ```
   📡 TEST-GPS-001: Attempting to connect to GPS server...
   📡 TEST-GPS-001: ✅ Connected to GPS server
   ```

3. **Connection Drops During Operation**:
   ```
   📡 TEST-GPS-001: Connection closed by server - will reconnect
   📡 TEST-GPS-001: Attempting to connect to GPS server...
   📡 TEST-GPS-001: GPS server not available - will retry in 5s
   ```

4. **Server Restored**:
   ```
   📡 TEST-GPS-001: Attempting to connect to GPS server...
   📡 TEST-GPS-001: ✅ Connected to GPS server
   ```

## Deployment Considerations

### ✅ Suitable For:
- Real hardware GPS devices (ESP32, etc.)
- Unreliable network environments
- Long-running deployments
- Autonomous vehicle operations
- Remote/distributed systems

### ⚠️ Considerations:
- **Buffer Overflow**: Long disconnections cause data loss
- **Retry Delay**: 5s delay may cause ~5s gap in telemetry after reconnect
- **Network Resources**: Continuous retry attempts consume minimal resources
- **Logging**: Verbose logging during disconnection (by design)

### 🔧 Tuning Parameters:

**For Unstable Networks**:
```python
connection_retry_delay = 2.0  # Faster reconnection
max_consecutive_errors = 5    # More tolerance
```

**For Stable Networks**:
```python
connection_retry_delay = 10.0  # Less aggressive retry
max_consecutive_errors = 2     # Faster failover
```

**For Critical Systems**:
```python
connection_retry_delay = 1.0   # Immediate retry
max_consecutive_errors = 10    # High tolerance
# Consider increasing buffer capacity in RxTxBuffer
```

## Code Changes

### Modified Files
- `arknet_transit_simulator/vehicle/gps_device/device.py`
  - Rewrote `_async_transmitter()` method
  - Added `import websockets` for exception handling
  - Added comprehensive error handling and reconnection logic

### New Files
- `test_gps_reconnection.py` - Test script for verification

## Backward Compatibility

✅ **Fully Backward Compatible**
- No API changes
- No configuration changes required
- Existing code continues to work
- Reconnection happens automatically

## Future Enhancements

1. **Configurable Retry Parameters**:
   ```python
   gps_device = GPSDevice(
       device_id="GPS-001",
       ws_transmitter=transmitter,
       plugin_config={...},
       reconnect_config={
           "retry_delay": 5.0,
           "max_errors": 3
       }
   )
   ```

2. **Connection Status Callback**:
   ```python
   def on_connection_status_change(connected: bool):
       if connected:
           logger.info("GPS connected")
       else:
           logger.warning("GPS disconnected")
   
   gps_device.on_connection_change = on_connection_status_change
   ```

3. **Metrics and Monitoring**:
   - Track reconnection count
   - Monitor connection uptime
   - Alert on excessive disconnections
   - Buffer overflow events

4. **Adaptive Retry Delay**:
   - Exponential backoff for persistent failures
   - Faster retry after first failure
   - Rate limiting for server protection

## Summary

The GPS device now implements robust reconnection logic suitable for real-world hardware deployment:

✅ Automatically reconnects when server becomes available  
✅ Handles connection drops during operation gracefully  
✅ Continues data collection during disconnection  
✅ Resumes transmission when connection restored  
✅ No manual intervention required  
✅ Suitable for isolated hardware devices  

This makes the GPS device truly resilient and ready for production deployment in environments with unreliable network connectivity.
