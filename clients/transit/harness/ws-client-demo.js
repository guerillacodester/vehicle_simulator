const WebSocket = require('ws');

const ws = new WebSocket('ws://localhost:4001/ws');
ws.on('open', () => console.log('[demo] connected to ws://localhost:4001/ws'));
ws.on('message', (m) => {
  try {
    const p = JSON.parse(m.toString());
    console.log('[demo] received', p.type, 'routeId=', p.routeId, 'vehicles=', p.vehicles.length);
  } catch (e) {
    console.log('[demo] raw', m.toString());
  }
});
ws.on('close', () => console.log('[demo] connection closed'));
