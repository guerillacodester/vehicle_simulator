const fetch = require('node-fetch');

async function testGraphQL() {
  const query = `
    query GetRouteGeometry {
      routeGeometry(routeName: "1") {
        success
        routeName
        coordinateCount
        segmentCount
        metrics {
          totalPoints
          estimatedLengthKm
          segments
          reversedCount
        }
        coordinates
      }
    }
  `;

  try {
    const response = await fetch('http://localhost:1337/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    const result = await response.json();
    
    if (result.errors) {
      console.error('GraphQL Errors:', JSON.stringify(result.errors, null, 2));
    } else {
      console.log('Success!');
      console.log('Route:', result.data.routeGeometry.routeName);
      console.log('Total Points:', result.data.routeGeometry.coordinateCount);
      console.log('Segments:', result.data.routeGeometry.segmentCount);
      console.log('Length (km):', result.data.routeGeometry.metrics.estimatedLengthKm);
      console.log('Reversed:', result.data.routeGeometry.metrics.reversedCount);
      console.log('\nFirst 5 coordinates:');
      console.log(result.data.routeGeometry.coordinates.slice(0, 5));
      console.log(`\n... and ${result.data.routeGeometry.coordinateCount - 5} more coordinates`);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

testGraphQL();
