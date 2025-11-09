/**
 * Test script to fetch route shapes from Strapi and validate terminus distance
 * 
 * Usage: node test_route_shapes.js [route_id]
 * Example: node test_route_shapes.js 1
 */

// Use Node's built-in fetch (Node 18+) to avoid extra dependencies
const STRAPI_URL = process.env.STRAPI_URL || 'http://localhost:1337/api';

/**
 * Calculate distance between two lat/lng points using Haversine formula
 * Returns distance in kilometers
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
  const R = 6371; // Earth's radius in km
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  
  const a = 
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  const distance = R * c;
  
  return distance;
}

function toRad(degrees) {
  return degrees * (Math.PI / 180);
}

// Fetch all routes from Strapi
async function fetchAllRoutes() {
  console.log('\nFetching all routes to verify existence...');
  try {
    const response = await fetch(`${STRAPI_URL}/routes`);
    const data = await response.json();
    
    if (response.ok) {
      console.log('\nAvailable Routes:', data);
    } else {
      console.error('Error fetching routes:', data);
    }
  } catch (error) {
    console.error('Error fetching all routes:', error);
  }
}

// Fetch specific route details from Strapi
async function testRouteShapes(routeId) {
  console.log(`\nTesting Route Shapes for Route ID: ${routeId}`);
  try {
    const response = await fetch(`${STRAPI_URL}/routes/${routeId}`);
    const data = await response.json();
    
    if (response.ok) {
      console.log('\nRoute Details:', data);
    } else {
      console.error(`Error fetching route ${routeId}:`, data);
    }
  } catch (error) {
    console.error(`Error fetching route ${routeId}:`, error);
  }
}

// Get route ID from command line or use default
const routeId = process.argv[2] || '1';
fetchAllRoutes().then(() => testRouteShapes(routeId));
