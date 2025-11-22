const open = require('open');

async function run() {
  // Open Next.js page that will handle login in browser context
  // This ensures cookies are properly set in the browser and CORS works
  console.log('Opening browser to authenticate...');
  await open('http://localhost:3000/auth-test-valid');
}

run();
