import { TelemetryDataProvider } from '../TelemetryDataProvider';

// Integration test - connects to real GPSCentCom server
// Run this with the server and simulator running

const GPSCENTCOM_URL = process.env.GPSCENTCOM_URL || 'http://localhost:5000';
const TEST_DURATION = 10000; // 10 seconds

describe('TelemetryDataProvider - Integration Test', () => {
  let provider: TelemetryDataProvider;

  beforeAll(() => {
    console.log('\n╔══════════════════════════════════════════════════════════╗');
    console.log('║  INTEGRATION TEST: Real GPSCentCom Server Connection   ║');
    console.log('╚══════════════════════════════════════════════════════════╝');
    console.log(`Connecting to: ${GPSCENTCOM_URL}`);
    console.log('Ensure GPSCentCom server and vehicle simulator are running!\n');
  });

  beforeEach(() => {
    provider = new TelemetryDataProvider(GPSCENTCOM_URL);
  });

  afterEach(() => {
    provider.disconnect();
  });

  it('should connect to real GPSCentCom server and receive telemetry', (done) => {
    console.log('=== Starting Real Telemetry Stream Test ===\n');
    
    let connectionEstablished = false;
    let snapshotReceived = false;
    let updateCount = 0;
    const receivedDevices = new Set<string>();

    // Monitor connection status
    provider.onStatus((state) => {
      console.log(`[Connection] State: ${state}`);
      
      if (state === 'connected') {
        connectionEstablished = true;
        console.log('[Connection] ✓ Successfully connected to GPSCentCom server\n');
      } else if (state === 'error') {
        console.error('[Connection] ✗ Failed to connect - ensure server is running!');
        done(new Error('Failed to connect to GPSCentCom server'));
      }
    });

    // Subscribe to vehicle updates
    provider.subscribe((vehicles) => {
      updateCount++;
      
      if (!snapshotReceived) {
        console.log(`[Snapshot] Received initial state with ${vehicles.length} vehicle(s)`);
        snapshotReceived = true;
      } else {
        console.log(`\n[Update #${updateCount}] Received data for ${vehicles.length} vehicle(s)`);
      }

      // Log each vehicle's data
      vehicles.forEach(vehicle => {
        receivedDevices.add(vehicle.deviceId);
        console.log(`  📍 Vehicle: ${vehicle.deviceId}`);
        console.log(`     Position: (${vehicle.lat.toFixed(6)}, ${vehicle.lon.toFixed(6)})`);
        console.log(`     Speed: ${vehicle.speed ?? vehicle.speed_m_s ?? 'N/A'} m/s`);
        console.log(`     Heading: ${vehicle.heading ?? 'N/A'}°`);
        console.log(`     Route: ${vehicle.route ?? 'N/A'}`);
        console.log(`     Last Seen: ${vehicle.lastSeen ?? vehicle.timestamp ?? 'N/A'}`);
      });

      // Validate we're receiving real data
      if (vehicles.length > 0) {
        const firstVehicle = vehicles[0];
        expect(firstVehicle).toHaveProperty('deviceId');
        expect(firstVehicle).toHaveProperty('lat');
        expect(firstVehicle).toHaveProperty('lon');
        expect(typeof firstVehicle.lat).toBe('number');
        expect(typeof firstVehicle.lon).toBe('number');
      }
    });

    // Connect to server
    provider.connect();

    // Run test for specified duration
    setTimeout(() => {
      console.log('\n=== Test Summary ===');
      console.log(`Connection established: ${connectionEstablished ? '✓' : '✗'}`);
      console.log(`Total updates received: ${updateCount}`);
      console.log(`Unique vehicles tracked: ${receivedDevices.size}`);
      console.log(`Devices: [${Array.from(receivedDevices).join(', ')}]`);
      
      if (connectionEstablished && updateCount > 0) {
        console.log('\n✓ Integration test PASSED - Real telemetry received!\n');
        done();
      } else if (!connectionEstablished) {
        done(new Error('Failed to establish connection to GPSCentCom server'));
      } else {
        console.log('\n⚠ Warning: Connected but no telemetry received. Is the simulator running?\n');
        done();
      }
    }, TEST_DURATION);
  }, TEST_DURATION + 2000);
});
