/**
 * Custom routes for direct GeoJSON import from file system
 */

export default {
  routes: [
    {
      method: 'POST',
      path: '/countries/:id/import-geojson',
      handler: 'import-geojson.importFromFile',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/countries/:id/import-geojson-direct',
      handler: 'import-geojson.importDirect',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
