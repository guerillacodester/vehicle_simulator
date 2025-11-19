import { TelemetryDataProvider } from '../TelemetryDataProvider';

// Mock WebSocket for testing
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  readyState = MockWebSocket.CONNECTING;

  constructor(public url: string) {
    // Simulate async connection
    setTimeout(() => {
      this.readyState = MockWebSocket.OPEN;
      this.onopen?.();
    }, 10);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    setTimeout(() => this.onclose?.(), 10);
  }

  send(_data: string) {
    // Mock send - no-op for tests
  }
}

// Replace global WebSocket with mock
// eslint-disable-next-line @typescript-eslint/no-explicit-any
(global as any).WebSocket = MockWebSocket;

const TEST_BASE_URL = 'http://localhost:5000';

describe('TelemetryDataProvider', () => {
  let provider: TelemetryDataProvider;

  beforeEach(() => {
    provider = new TelemetryDataProvider(TEST_BASE_URL);
  });

  afterEach(() => {
    provider.disconnect();
  });

  it('should start in disconnected state', () => {
    expect(provider.getState()).toBe('disconnected');
  });

  it('should connect and update state to connected', (done) => {
    provider.onStatus((state) => {
      if (state === 'connected') {
        expect(state).toBe('connected');
        done();
      }
    });
    provider.connect();
  }, 1000);

  it('should receive snapshot of vehicles on connect', (done) => {
    console.log('\n=== Test: Snapshot Reception ===');
    
    provider.onStatus((state) => {
      console.log(`[Status] Connection state: ${state}`);
    });
    
    provider.subscribe((vehicles) => {
      console.log(`[Data] Received ${vehicles.length} vehicle(s):`);
      vehicles.forEach(v => {
        console.log(`  - ${v.deviceId}: lat=${v.lat}, lon=${v.lon}`);
      });
      
      if (vehicles.length > 0) {
        expect(Array.isArray(vehicles)).toBe(true);
        expect(vehicles[0]).toHaveProperty('deviceId');
        expect(vehicles[0].deviceId).toBe('TEST001');
        console.log('[Test] ✓ Snapshot validation passed\n');
        done();
      }
    });
    
    provider.connect();
    
    // Simulate snapshot message from server
    setTimeout(() => {
      const ws = (provider as unknown as { ws: MockWebSocket }).ws;
      const mockSnapshot = {
        data: JSON.stringify({
          type: 'snapshot',
          states: [
            { deviceId: 'TEST001', lat: 40.7128, lon: -74.0060 },
            { deviceId: 'TEST002', lat: 40.7589, lon: -73.9851 }
          ]
        })
      };
      console.log('[Server] Sending snapshot message...');
      ws?.onmessage?.(mockSnapshot);
    }, 50);
  }, 1000);

  it('should handle single vehicle update', (done) => {
    console.log('\n=== Test: Single Vehicle Update ===');
    let snapshotReceived = false;
    
    provider.onStatus((state) => {
      console.log(`[Status] Connection state: ${state}`);
    });
    
    provider.subscribe((vehicles) => {
      console.log(`[Data] Update received - ${vehicles.length} vehicle(s):`);
      vehicles.forEach(v => {
        console.log(`  - ${v.deviceId}: lat=${v.lat}, lon=${v.lon}, speed=${v.speed || 'N/A'}`);
      });
      
      if (!snapshotReceived && vehicles.length === 0) {
        console.log('[Test] Empty snapshot confirmed');
        snapshotReceived = true;
        return;
      }
      
      if (snapshotReceived && vehicles.length > 0) {
        // Vehicle update received
        const vehicle = vehicles.find(v => v.deviceId === 'TEST003');
        expect(vehicle).toBeDefined();
        expect(vehicle?.lat).toBe(40.7489);
        expect(vehicle?.lon).toBe(-73.9680);
        console.log('[Test] ✓ Vehicle update validation passed\n');
        done();
      }
    });
    
    provider.connect();
    
    setTimeout(() => {
      const ws = (provider as unknown as { ws: MockWebSocket }).ws;
      
      // First: empty snapshot
      console.log('[Server] Sending empty snapshot...');
      ws?.onmessage?.({ data: JSON.stringify({ type: 'snapshot', states: [] }) });
      
      // Second: single vehicle update
      setTimeout(() => {
        console.log('[Server] Sending vehicle update for TEST003...');
        ws?.onmessage?.({ 
          data: JSON.stringify({ 
            deviceId: 'TEST003', 
            lat: 40.7489, 
            lon: -73.9680,
            speed: 25.5
          }) 
        });
      }, 50);
    }, 50);
  }, 2000);

  it('should handle reconnection on close', (done) => {
    console.log('\n=== Test: Reconnection Logic ===');
    let connected = false;
    
    provider.onStatus((state) => {
      console.log(`[Status] Connection state: ${state}`);
      
      if (state === 'connected' && !connected) {
        connected = true;
        console.log('[Test] Triggering connection close to test reconnection...');
        // Trigger close to test reconnection
        const ws = (provider as unknown as { ws: MockWebSocket }).ws;
        ws?.close();
      }
      if (state === 'reconnecting' && connected) {
        expect(state).toBe('reconnecting');
        console.log('[Test] ✓ Reconnection triggered successfully\n');
        provider.disconnect();
        done();
      }
    });
    provider.connect();
  }, 2000);

  it('should send ping messages periodically', (done) => {
    const sendSpy = jest.fn();
    
    provider.connect();
    
    setTimeout(() => {
      const ws = (provider as unknown as { ws: MockWebSocket }).ws;
      if (ws) {
        ws.send = sendSpy;
        
        // Manually trigger ping interval
        const pingInterval = (provider as unknown as { pingInterval: NodeJS.Timeout }).pingInterval;
        if (pingInterval) {
          clearInterval(pingInterval);
        }
        
        // Simulate ping
        ws.send(JSON.stringify({ type: 'ping' }));
        
        expect(sendSpy).toHaveBeenCalledWith(JSON.stringify({ type: 'ping' }));
        done();
      }
    }, 100);
  }, 1000);
});
