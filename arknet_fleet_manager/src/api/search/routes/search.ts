/**
 * Search routes - defines API endpoints that match simulator expectations
 */

export default {
  routes: [
    // Vehicle-driver pairs endpoint (used by simulator)
    {
      method: 'GET',
      path: '/api/v1/search/vehicle-driver-pairs',
      handler: 'search.vehicleDriverPairs',
      config: {
        auth: false, // No authentication required for public access
      },
    },
    
    // Public vehicles endpoint
    {
      method: 'GET',
      path: '/api/v1/vehicles/public',
      handler: 'search.vehiclesPublic',
      config: {
        auth: false,
      },
    },
    
    // Public route by code
    {
      method: 'GET',
      path: '/api/v1/routes/public/:code',
      handler: 'search.routePublic',
      config: {
        auth: false,
      },
    },
    
    // Route geometry by code
    {
      method: 'GET',
      path: '/api/v1/routes/public/:code/geometry',
      handler: 'search.routeGeometry',
      config: {
        auth: false,
      },
    },
  ],
};