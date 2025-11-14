const fetch = require('node-fetch');

async function testRouteGeometryQuery(routeName) {
  const response = await fetch('http://localhost:1337/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: `query { routeGeometry(routeName: "${routeName}") { success routeName distanceKm coordinateCount segmentCount metrics { totalPoints estimatedLengthKm segments reversedCount } coordinates } }`
    })
  });
  const result = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

// Replace 'TEST_ROUTE' with a valid route name
const routeName = process.argv[2] || 'TEST_ROUTE';
testRouteGeometryQuery(routeName);
