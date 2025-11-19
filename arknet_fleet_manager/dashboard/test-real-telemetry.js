// Quick script to connect to GPSCentCom server and see real telemetry
// Run with: node test-real-telemetry.js

const WebSocket = require('ws');

// AUTH_TOKEN from gpscentcom_server/.env
const GPSCENTCOM_URL = process.env.GPSCENTCOM_URL || 'ws://localhost:5000/ws';
const AUTH_TOKEN = process.env.AUTH_TOKEN || 'supersecrettoken';
const TEST_DURATION = 15000; // 15 seconds

console.log('\n╔══════════════════════════════════════════════════════════╗');
console.log('║  REAL TELEMETRY TEST: GPSCentCom WebSocket Connection   ║');
console.log('╚══════════════════════════════════════════════════════════╝');
console.log(`Connecting to: ${GPSCENTCOM_URL}`);
console.log(`Using auth token: ${AUTH_TOKEN}`);
console.log('Ensure GPSCentCom server and vehicle simulator are running!\n');

// WebSocket with auth header
const ws = new WebSocket(GPSCENTCOM_URL, {
  headers: {
    'Authorization': `Bearer ${AUTH_TOKEN}`
  }
});

let messageCount = 0;
let snapshotReceived = false;
const devices = new Set();

ws.on('open', () => {
  console.log('[Connection] ✓ WebSocket connected successfully\n');
});

ws.on('message', (data) => {
  messageCount++;
  
  try {
    const message = JSON.parse(data.toString());
    
    console.log(`\n[Message #${messageCount}] Type: ${message.type || 'unknown'}`);
    console.log('Raw message:', JSON.stringify(message, null, 2));
    
    // Handle different message types
    if (message.type === 'snapshot') {
      snapshotReceived = true;
      const vehicleCount = message.vehicles ? message.vehicles.length : 0;
      console.log(`\n[Snapshot] Received initial state with ${vehicleCount} vehicle(s)`);
      
      if (message.vehicles) {
        message.vehicles.forEach(vehicle => {
          devices.add(vehicle.deviceId || vehicle.device_id);
          console.log(`  📍 Vehicle: ${vehicle.deviceId || vehicle.device_id}`);
          console.log(`     Position: (${vehicle.lat}, ${vehicle.lon})`);
          console.log(`     Speed: ${vehicle.speed ?? vehicle.speed_m_s ?? 'N/A'}`);
          console.log(`     Heading: ${vehicle.heading ?? 'N/A'}°`);
          console.log(`     Route: ${vehicle.route ?? 'N/A'}`);
        });
      }
    } else if (message.type === 'update') {
      const deviceId = message.deviceId || message.device_id;
      devices.add(deviceId);
      console.log(`\n[Update] Vehicle: ${deviceId}`);
      console.log(`  Position: (${message.lat}, ${message.lon})`);
      console.log(`  Speed: ${message.speed ?? message.speed_m_s ?? 'N/A'}`);
      console.log(`  Heading: ${message.heading ?? 'N/A'}°`);
      console.log(`  Route: ${message.route ?? 'N/A'}`);
      console.log(`  Timestamp: ${message.timestamp ?? message.lastSeen ?? 'N/A'}`);
    } else {
      console.log('[Unknown] Message format not recognized');
    }
    
  } catch (err) {
    console.error('[Error] Failed to parse message:', err.message);
    console.log('Raw data:', data.toString());
  }
});

ws.on('error', (error) => {
  console.error('\n[Connection] ✗ WebSocket error:', error.message);
  console.error('Make sure GPSCentCom server is running on port 5000!');
});

ws.on('close', (code, reason) => {
  console.log(`\n[Connection] WebSocket closed (code: ${code}, reason: ${reason || 'none'})`);
});

// Test summary after duration
setTimeout(() => {
  console.log('\n\n╔══════════════════════════════════════════════════════════╗');
  console.log('║                     TEST SUMMARY                        ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log(`Total messages received: ${messageCount}`);
  console.log(`Snapshot received: ${snapshotReceived ? '✓' : '✗'}`);
  console.log(`Unique devices tracked: ${devices.size}`);
  console.log(`Devices: [${Array.from(devices).join(', ')}]`);
  
  if (messageCount > 0) {
    console.log('\n✓ SUCCESS - Real telemetry received from GPSCentCom server!\n');
  } else {
    console.log('\n⚠ WARNING - No telemetry received. Check if server and simulator are running.\n');
  }
  
  ws.close();
  process.exit(0);
}, TEST_DURATION);

// Handle CTRL+C
process.on('SIGINT', () => {
  console.log('\n\nTest interrupted by user');
  ws.close();
  process.exit(0);
});
