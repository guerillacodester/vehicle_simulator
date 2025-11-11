const fetch = require('node-fetch');

const query = `
  query {
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
      distanceKm
    }
  }
`;

fetch('http://localhost:1337/graphql', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query })
})
  .then(res => res.json())
  .then(json => {
    console.log(JSON.stringify(json, null, 2));
  })
  .catch(err => {
    console.error('Error:', err);
  });
