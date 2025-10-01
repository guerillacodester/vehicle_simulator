const fetch = require('node-fetch');

async function testStrapiAPI() {
  try {
    console.log('Testing Strapi API endpoints...\n');

    // Test basic connectivity
    const healthCheck = await fetch('http://localhost:1337');
    console.log(`Health check: ${healthCheck.status} ${healthCheck.statusText}`);

    // Test each content type
    const contentTypes = ['drivers', 'vehicles', 'routes', 'depots'];
    
    for (const type of contentTypes) {
      try {
        const response = await fetch(`http://localhost:1337/api/${type}`);
        const data = await response.json();
        
        console.log(`\n=== ${type.toUpperCase()} API ===`);
        console.log(`Status: ${response.status} ${response.statusText}`);
        
        if (response.ok) {
          console.log(`Data count: ${data.data ? data.data.length : 0}`);
          if (data.data && data.data.length > 0) {
            console.log('Sample record:', data.data[0]);
          }
        } else {
          console.log('Error:', data);
        }
      } catch (error) {
        console.log(`\n=== ${type.toUpperCase()} API ===`);
        console.log('Error:', error.message);
      }
    }

  } catch (error) {
    console.error('Failed to test API:', error.message);
  }
}

testStrapiAPI();