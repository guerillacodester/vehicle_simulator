/**
 * Test script for fetchRouteGeometry service method
 * Run with: node test_route_geometry.js
 */

const fetch = require('node-fetch');

async function testRouteGeometry() {
  console.log('Testing fetchRouteGeometry for Route 1...\n');

  try {
    // Test via GraphQL query to route service
    const query = `
      query {
        routes(filters: { route_short_name: { eq: "1" } }) {
          data {
            id
            attributes {
              route_short_name
              route_long_name
            }
          }
        }
      }
    `;

    const response = await fetch('http://localhost:1337/graphql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query }),
    });

    const result = await response.json();
    console.log('Route query result:', JSON.stringify(result, null, 2));

    if (result.data?.routes?.data?.[0]) {
      const route = result.data.routes.data[0];
      console.log(`\nFound Route: ${route.attributes.route_short_name} - ${route.attributes.route_long_name}`);
      console.log('\nTo test fetchRouteGeometry, you can call it from Strapi console:');
      console.log('  await strapi.service("api::route.route").fetchRouteGeometry("1")');
    }

  } catch (error) {
    console.error('Error:', error.message);
  }
}

testRouteGeometry();
