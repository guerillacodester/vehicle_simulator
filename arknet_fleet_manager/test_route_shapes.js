/**
 * Test script to fetch route shapes from Strapi and validate terminus distance
 * 
 * Usage: node test_route_shapes.js [route_id]
 * Example: node test_route_shapes.js 1
 */

const axios = require('axios');

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

async function testRouteShapes(routeId) {
  console.log('='.repeat(60));
  console.log(`Testing Route Shapes for Route ID: ${routeId}`);
  console.log('='.repeat(60));
  
  try {
    // Fetch route details from Strapi
    console.log(`\n📡 Fetching route from: ${STRAPI_URL}/routes/${routeId}`);
    const response = await axios.get(`${STRAPI_URL}/routes/${routeId}`);
    
    console.log('\n✅ Response received!');
    console.log('Status:', response.status);
    
    const routeData = response.data.data;
    console.log('\n📋 Route Info:');
    console.log('  ID:', routeData.id);
    console.log('  Code:', routeData.attributes?.code);
    console.log('  Name:', routeData.attributes?.name);
    console.log('  Origin:', routeData.attributes?.origin);
    console.log('  Destination:', routeData.attributes?.destination);
    
    // Check if geometry exists
    const geometry = routeData.attributes?.geometry;
    if (!geometry) {
      console.error('\n❌ ERROR: No geometry found in response!');
      return;
    }
    
    console.log('\n🗺️  Geometry Info:');
    console.log('  Type:', geometry.type);
    console.log('  Coordinates count:', geometry.coordinates?.length || 0);
    
    if (!geometry.coordinates || geometry.coordinates.length < 2) {
      console.error('\n❌ ERROR: Not enough coordinates to calculate distance!');
      return;
    }
    
    // Get first and last points (terminus)
    const firstPoint = geometry.coordinates[0];
    const lastPoint = geometry.coordinates[geometry.coordinates.length - 1];
    
    console.log('\n📍 Terminus Points:');
    console.log('  Start (Origin):', firstPoint);
    console.log('  End (Destination):', lastPoint);
    
    // Calculate distance
    const distance = calculateDistance(
      firstPoint[1], firstPoint[0],  // lat, lon of start
      lastPoint[1], lastPoint[0]      // lat, lon of end
    );
    
    console.log('\n📏 Distance Calculation:');
    console.log('  Straight-line distance:', distance.toFixed(3), 'km');
    console.log('  Straight-line distance:', (distance * 0.621371).toFixed(3), 'miles');
    
    // Calculate total path distance (sum of all segments)
    let totalPathDistance = 0;
    for (let i = 0; i < geometry.coordinates.length - 1; i++) {
      const point1 = geometry.coordinates[i];
      const point2 = geometry.coordinates[i + 1];
      totalPathDistance += calculateDistance(
        point1[1], point1[0],
        point2[1], point2[0]
      );
    }
    
    console.log('  Total path distance:', totalPathDistance.toFixed(3), 'km');
    console.log('  Total path distance:', (totalPathDistance * 0.621371).toFixed(3), 'miles');
    
    // Validation checks
    console.log('\n✅ Validation:');
    if (distance > 0 && distance < 100) {
      console.log('  ✓ Distance seems reasonable for a route');
    } else {
      console.log('  ⚠️  Distance might be incorrect (>100km or 0)');
    }
    
    if (totalPathDistance > distance) {
      console.log('  ✓ Path distance > straight line (expected)');
    } else {
      console.log('  ⚠️  Path distance should be > straight line');
    }
    
    if (geometry.coordinates.length > 10) {
      console.log('  ✓ Sufficient shape points for detailed route');
    } else {
      console.log('  ⚠️  Low number of shape points');
    }
    
    console.log('\n' + '='.repeat(60));
    console.log('Test completed successfully! ✅');
    console.log('='.repeat(60) + '\n');
    
  } catch (error) {
    console.error('\n❌ ERROR:', error.message);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', JSON.stringify(error.response.data, null, 2));
    }
  }
}

// Get route ID from command line or use default
const routeId = process.argv[2] || '1';
testRouteShapes(routeId);
