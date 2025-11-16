// Enhanced test for optimized Redis caching for route geometry
const fetch = require('node-fetch');

const GRAPHQL_URL = 'http://localhost:1337/graphql';

const query = `
  query GetRouteGeometry($routeName: String!) {
    routeGeometry(routeName: $routeName) {
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
      distanceKm
    }
  }
`;

async function testOptimizedCache() {
  console.log('\n🚀 Testing OPTIMIZED Redis Cache for Route Geometry 🚀\n');

  // Test 1: First request (cache miss)
  console.log('📊 Test 1: First request (CACHE MISS expected)');
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
  console.log(`⏱️  Response time: ${time1}ms`);
  console.log('📈 Metrics:', data1.data?.routeGeometry?.metrics);

  // Test 2: Second request (cache hit)
  console.log('\n📊 Test 2: Second request (CACHE HIT expected)');
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
  console.log(`⏱️  Response time: ${time2}ms`);
  console.log('📈 Metrics:', data2.data?.routeGeometry?.metrics);

  // Performance analysis
  const speedup = (time1 / time2).toFixed(2);
  const efficiency = time2 < 50 ? 'EXCELLENT' : time2 < 100 ? 'GOOD' : 'NEEDS OPTIMIZATION';

  console.log(`\n🎯 Performance Results:`);
  console.log(`   Speedup: ${speedup}x faster`);
  console.log(`   Cache Efficiency: ${efficiency}`);
  console.log(`   First request: ${time1}ms (computation + storage)`);
  console.log(`   Cached request: ${time2}ms (retrieval + decompression)`);

  // Test 3: Multiple routes to test cache isolation
  console.log('\n📊 Test 3: Multiple routes cache isolation');
  const routes = ['1', '2', '3'];
  for (const route of routes) {
    console.log(`   Testing route ${route}...`);
    const start = Date.now();
    const response = await fetch(GRAPHQL_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        variables: { routeName: route }
      })
    });
    const data = await response.json();
    const time = Date.now() - start;
    console.log(`     Route ${route}: ${time}ms (${data.data?.routeGeometry?.coordinateCount || 0} coordinates)`);
  }

  console.log('\n📋 Check the Strapi console for detailed [Redis Cache] logs!');
  console.log('🔍 Look for compression ratios, access counts, and TTL adjustments.');
  console.log('\n✅ Route Geometry Cache Optimization Test Complete!\n');
}

testOptimizedCache().catch(console.error);
