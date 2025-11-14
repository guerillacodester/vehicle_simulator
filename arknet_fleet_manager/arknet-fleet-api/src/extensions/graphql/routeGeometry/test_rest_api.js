const fetch = require('node-fetch');

async function testRestAPI(routeName) {
  console.log(`\n=== Testing REST API for route: ${routeName} ===\n`);
  
  try {
    const response = await fetch(`http://localhost:1337/api/routes/${routeName}/geometry`);
    const result = await response.json();
    
    console.log('Status:', response.status);
    console.log('Response:', JSON.stringify(result, null, 2));
    
    if (result.success) {
      console.log('\n=== Summary ===');
      console.log('Route:', result.routeName);
      console.log('Distance (km):', result.distanceKm);
      console.log('Coordinates:', result.coordinateCount);
      console.log('Segments:', result.segmentCount);
      console.log('Message:', result.message);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Use route name from command line or default to "1"
const routeName = process.argv[2] || '1';
testRestAPI(routeName);
