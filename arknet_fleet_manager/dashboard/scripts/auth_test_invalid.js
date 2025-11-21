const fetch = require('node-fetch');
const open = require('open');

async function run() {
  // Simulate invalid user login
  const res = await fetch('http://localhost:7000/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username: 'invaliduser', password: 'invalidpass' })
  });
  const cookies = res.headers.get('set-cookie');
  console.log('Received cookies:', cookies);
  // Open telemetry wall demo page (browser will use cookies)
  await open('http://localhost:3000/telemetry-wall-demo');
}

run();
