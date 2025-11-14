const fetch = require('node-fetch');

async function listRoutes() {
  const response = await fetch('http://localhost:1337/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query: `query { routes { route_id route_short_name route_long_name } }`
    })
  });
  const result = await response.json();
  console.log(JSON.stringify(result, null, 2));
}

listRoutes();
