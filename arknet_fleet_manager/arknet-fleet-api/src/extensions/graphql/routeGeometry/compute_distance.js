const fetch = require('node-fetch');

async function computeDistanceFromAPI(routeName) {
  console.log(`\n=== Computing Distance for Route: ${routeName} ===\n`);
  
  try {
    const response = await fetch(`http://localhost:1337/api/routes/${routeName}/geometry`);
    const result = await response.json();
    
    if (result.success && result.coordinates) {
      const coords = result.coordinates;
      
      // Haversine formula to calculate distance between two lat/lng points
      function haversineDistance(lat1, lon1, lat2, lon2) {
        const R = 6371; // Earth's radius in kilometers
        const dLat = (lat2 - lat1) * Math.PI / 180;
        const dLon = (lon2 - lon1) * Math.PI / 180;
        const a = 
          Math.sin(dLat/2) * Math.sin(dLat/2) +
          Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
          Math.sin(dLon/2) * Math.sin(dLon/2);
        const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
        return R * c;
      }
      
      // Calculate total distance
      let totalDistance = 0;
      for (let i = 0; i < coords.length - 1; i++) {
        const [lon1, lat1] = coords[i];
        const [lon2, lat2] = coords[i + 1];
        const segmentDistance = haversineDistance(lat1, lon1, lat2, lon2);
        totalDistance += segmentDistance;
      }
      
      console.log('=== Distance Calculation Results ===');
      console.log(`Route: ${result.routeName}`);
      console.log(`Total Coordinates: ${coords.length}`);
      console.log(`Total Segments: ${coords.length - 1}`);
      console.log(`\nComputed Distance (Haversine): ${totalDistance.toFixed(6)} km`);
      console.log(`API Reported Distance: ${result.distanceKm} km`);
      console.log(`Difference: ${Math.abs(totalDistance - result.distanceKm).toFixed(6)} km`);
      console.log(`Match Percentage: ${((Math.min(totalDistance, result.distanceKm) / Math.max(totalDistance, result.distanceKm)) * 100).toFixed(2)}%`);
      
    } else {
      console.error('Failed to fetch route geometry:', result);
    }
  } catch (error) {
    console.error('Error:', error.message);
  }
}

// Use route name from command line or default to "1"
const routeName = process.argv[2] || '1';
computeDistanceFromAPI(routeName);
