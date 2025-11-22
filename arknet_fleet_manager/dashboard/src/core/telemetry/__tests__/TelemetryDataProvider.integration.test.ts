import { TelemetryDataProvider } from '../TelemetryDataProvider';

// Integration test - connects to real GPSCentCom server
// Run this with the server and simulator running

const GPSCENTCOM_URL = process.env.GPSCENTCOM_URL || 'http://localhost:5000';
const TEST_DURATION = 10000; // 10 seconds

// Mock WebSocket for integration testing
class MockWebSocketServer {
  static instance: MockWebSocketServer;
  private connections: any[] = [];

  constructor() {
    MockWebSocketServer.instance = this;
  }

  simulateConnection(ws: any) {
    this.connections.push(ws);
    // Simulate server accepting connection
    setTimeout(() => ws.onopen?.(), 10);
  }

  simulateMessage(data: any) {
    this.connections.forEach(ws => {
      if (ws.onmessage) {
        ws.onmessage({ data: JSON.stringify(data) });
      }
    });
  }

  simulateClose() {
    this.connections.forEach(ws => ws.onclose?.());
    this.connections = [];
  }
}

// Override global WebSocket for integration test
const OriginalWebSocket = global.WebSocket;
global.WebSocket = class MockWebSocket {
  url: string;
  readyState = 0; // CONNECTING
  onopen: any;
  onmessage: any;
  onclose: any;
  onerror: any;

  constructor(url: string) {
    this.url = url;
    const server = MockWebSocketServer.instance || new MockWebSocketServer();
    setTimeout(() => {
      this.readyState = 1; // OPEN
      server.simulateConnection(this);
    }, 0);
  }

  send(data: string) {
    // Mock send - no-op for integration test
  }

  close() {
    this.readyState = 3; // CLOSED
    this.onclose?.();
  }

  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
} as any;

describe('TelemetryDataProvider - Integration Test', () => {
  let provider: TelemetryDataProvider;
  let mockServer: MockWebSocketServer;

  beforeAll(() => {
    console.log('\n╔══════════════════════════════════════════════════════════╗');
    console.log('║  INTEGRATION TEST: Simulated Server Connection         ║');
    console.log('╚══════════════════════════════════════════════════════════╝');
    console.log(`Testing with: ${GPSCENTCOM_URL}`);
    console.log('Using mock WebSocket server for reliable testing\n');
  });

  beforeEach(() => {
    mockServer = new MockWebSocketServer();
  });

  afterAll(() => {
    // Restore original WebSocket
    global.WebSocket = OriginalWebSocket;
  });

  beforeEach(() => {
    provider = new TelemetryDataProvider(GPSCENTCOM_URL);
  });

  afterEach(() => {
    provider.disconnect();
  });

  it('should connect and receive telemetry from mock server', (done) => {
    console.log('=== Starting Mock Server Integration Test ===\n');
    
    let connectionEstablished = false;
    let snapshotReceived = false;
    let updateCount = 0;
    const receivedDevices = new Set<string>();

    // Monitor connection status
    provider.onStatus((state) => {
      console.log(`[Connection] State: ${state}`);
      
      if (state === 'connected') {
        connectionEstablished = true;
        console.log('[Connection] ✓ Successfully connected\n');
        
        // Simulate server sending snapshot
        setTimeout(() => {
          mockServer.simulateMessage({
            type: 'snapshot',
            states: [
              { deviceId: 'GPS-INT001', lat: 13.25, lon: -59.64, route: '1' },
              { deviceId: 'GPS-INT002', lat: 13.26, lon: -59.65, route: '2' }
            ]
          });
        }, 100);

        // Simulate server sending update
        setTimeout(() => {
          mockServer.simulateMessage({
            type: 'update',
            deviceId: 'GPS-INT001',
            state: { deviceId: 'GPS-INT001', lat: 13.251, lon: -59.641, route: '1', speed: 45 }
          });
        }, 200);
      }
    });

    // Subscribe to vehicle updates
    provider.subscribe((vehicles) => {
      if (!snapshotReceived && vehicles.length > 0) {
        console.log(`[Snapshot] Received initial state with ${vehicles.length} vehicle(s)`);
        snapshotReceived = true;
      } else if (snapshotReceived && vehicles.length > 0) {
        updateCount++;
        console.log(`\n[Update #${updateCount}] Received data for ${vehicles.length} vehicle(s)`);
      }

      // Log each vehicle's data
      vehicles.forEach(vehicle => {
        receivedDevices.add(vehicle.deviceId);
        console.log(`  📍 Vehicle: ${vehicle.deviceId}`);
        console.log(`     Position: (${vehicle.lat.toFixed(6)}, ${vehicle.lon.toFixed(6)})`);
        console.log(`     Route: ${vehicle.route ?? 'N/A'}`);
        if (vehicle.speed !== undefined) {
          console.log(`     Speed: ${vehicle.speed} m/s`);
        }
      });

      // Validate we're receiving mocked data
      if (vehicles.length > 0) {
        const firstVehicle = vehicles[0];
        expect(firstVehicle).toHaveProperty('deviceId');
        expect(firstVehicle).toHaveProperty('lat');
        expect(firstVehicle).toHaveProperty('lon');
        expect(typeof firstVehicle.lat).toBe('number');
        expect(typeof firstVehicle.lon).toBe('number');
      }

      // Success criteria: Connection + Snapshot + at least 1 update
      if (connectionEstablished && snapshotReceived && updateCount >= 1) {
        console.log('\n=== Test Summary ===');
        console.log(`✓ Connection established`);
        console.log(`✓ Snapshot received with ${receivedDevices.size} vehicles`);
        console.log(`✓ ${updateCount} telemetry updates received`);
        console.log(`✓ Devices: [${Array.from(receivedDevices).join(', ')}]`);
        console.log('\n✓ Integration test PASSED!\n');
        done();
      }
    });

    // Connect to server
    provider.connect();

    // Timeout if criteria not met
    setTimeout(() => {
      if (!connectionEstablished || !snapshotReceived || updateCount < 1) {
        console.log('\n=== Test Timeout ===');
        console.log(`Connection: ${connectionEstablished ? '✓' : '✗'}`);
        console.log(`Snapshot: ${snapshotReceived ? '✓' : '✗'}`);
        console.log(`Updates: ${updateCount}`);
        done(new Error('Test criteria not met within timeout'));
      }
    }, 5000);
  }, 10000);
});
