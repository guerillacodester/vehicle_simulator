const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const routes = require('./data/routes.json');

const app = express();
app.use(express.json());

app.get('/routes', (req, res) => {
  res.json(routes.map(r => ({ id: r.id, code: r.code, name: r.name, origin: r.origin, destination: r.destination })));
});

app.get('/routes/:id', (req, res) => {
  const r = routes.find(x => x.id === req.params.id || x.code === req.params.id);
  if (!r) return res.status(404).json({ error: 'not found' });
  res.json(r);
});

const server = http.createServer(app);
const wss = new WebSocket.Server({ server, path: '/ws' });

// Simple simulator: emit vehicle positions for each route every 2s
function startEmitter() {
  setInterval(() => {
    routes.forEach(route => {
      // create 3 vehicles with random jitter near first coordinate
      const vehicles = [0,1,2].map(i => ({
        vehicleId: `${route.id}-BUS-${i+1}`,
        routeId: route.id,
        lat: route.geometry.coordinates[0][1] + (Math.random()-0.5)*0.01,
        lon: route.geometry.coordinates[0][0] + (Math.random()-0.5)*0.01,
        speedKmh: 40 + Math.random()*20,
        heading: Math.random()*360,
        timestamp: new Date().toISOString()
      }));

      const msg = JSON.stringify({ type: 'vehicle:update', routeId: route.id, vehicles });
      wss.clients.forEach(client => {
        if (client.readyState === WebSocket.OPEN) client.send(msg);
      });
    });
  }, 2000);
}

wss.on('connection', (ws) => {
  console.log('[mock-ws] client connected');
  ws.on('close', () => console.log('[mock-ws] client disconnected'));
});

server.listen(4001, () => {
  console.log('Mock transit server listening on http://localhost:4001');
  startEmitter();
});
