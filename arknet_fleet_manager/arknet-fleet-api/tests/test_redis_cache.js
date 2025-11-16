// Test Redis caching for route geometry
const fetch = require('node-fetch');

const GRAPHQL_URL = 'http://localhost:1337/graphql';

const query = `
  query GetRouteGeometry($routeName: String!) {
    routeGeometry(routeName: $routeName) {
      metrics {
        totalPoints
        estimatedLengthKm
        segments
        reversedCount
      }
      coords
    }
  }
`;

async function testCache() {
  console.log('\n=== Testing Redis Cache for Route Geometry ===\n');
  
  console.log('First request (should be CACHE MISS):');
  const start1 = Date.now();
  const response1 = await fetch(GRAPHQL_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      variables: { routeName: '1' }
    })
  });
  const data1 = await response1.json();
  const time1 = Date.now() - start1;
  console.log(`Response time: ${time1}ms`);
  console.log('Metrics:', data1.data?.routeGeometry?.metrics);
  
  console.log('\nSecond request (should be CACHE HIT):');
  const start2 = Date.now();
  const response2 = await fetch(GRAPHQL_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      variables: { routeName: '1' }
    })
  });
  const data2 = await response2.json();
  const time2 = Date.now() - start2;
  console.log(`Response time: ${time2}ms`);
  console.log('Metrics:', data2.data?.routeGeometry?.metrics);
  
  console.log(`\nSpeedup: ${(time1 / time2).toFixed(2)}x faster`);
  console.log('\nCheck the Strapi console for [Redis Cache] logs!\n');
}

testCache().catch(console.error);
