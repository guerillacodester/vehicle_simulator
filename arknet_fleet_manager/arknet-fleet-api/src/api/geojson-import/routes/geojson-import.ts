/**
 * GeoJSON Import API Routes
 * Handles streaming import of large GeoJSON files with Socket.IO progress updates
 * 
 * These endpoints are called by admin UI action buttons:
 * - Highway import (road network)
 * - Amenity import (POIs - shops, restaurants, etc.)
 * - Landuse import (zones for spawning weights)
 * - Building import (building footprints - 658MB file)
 * - Admin boundaries import (regions, parishes, districts)
 */

export default {
  routes: [
    // Import highway.geojson (road network for reverse geocoding)
    {
      method: 'POST',
      path: '/import-geojson/highway',
      handler: 'geojson-import.importHighway',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Import amenity.geojson (POIs for passenger spawning)
    {
      method: 'POST',
      path: '/import-geojson/amenity',
      handler: 'geojson-import.importAmenity',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Import landuse.geojson (zones with population density)
    {
      method: 'POST',
      path: '/import-geojson/landuse',
      handler: 'geojson-import.importLanduse',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Import building.geojson (building footprints - LARGE FILE: 658MB)
    {
      method: 'POST',
      path: '/import-geojson/building',
      handler: 'geojson-import.importBuilding',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Import admin boundaries (regions, parishes, districts from admin_level_*.geojson)
    {
      method: 'POST',
      path: '/import-geojson/admin',
      handler: 'geojson-import.importAdmin',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Health check endpoint for testing
    {
      method: 'GET',
      path: '/import-geojson/health',
      handler: 'geojson-import.health',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
