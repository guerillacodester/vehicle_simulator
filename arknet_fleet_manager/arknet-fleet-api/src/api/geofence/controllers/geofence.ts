import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::geofence.geofence' as any, ({ strapi }) => ({
  /**
   * Override find method to add nearby highways and POIs when lat/lon is provided
   */
  async find(ctx: any) {
    const { lat, lon, distance = 50 } = ctx.query;

    // If lat/lon provided, find nearby highways and POIs
    if (lat && lon) {
      try {
        const latitude = parseFloat(lat as string);
        const longitude = parseFloat(lon as string);
        const distanceMeters = parseFloat(distance as string);

        if (isNaN(latitude) || isNaN(longitude) || isNaN(distanceMeters)) {
          return ctx.badRequest('Invalid parameters: lat, lon, and distance must be valid numbers');
        }

        // Query the database directly using plain SQL
        const query = `
          SELECT * FROM find_nearby_features(${latitude}, ${longitude}, ${distanceMeters})
        `;
        
        const result = await strapi.db.connection.raw(query);
        const rows = result.rows || result[0] || [];

        // Group results by feature type
        const highways: any[] = [];
        const pois: any[] = [];

        rows.forEach((row: any) => {
          // Parse feature_data if it's a string, otherwise use as-is
          const featureData = typeof row.feature_data === 'string' 
            ? JSON.parse(row.feature_data) 
            : row.feature_data;

          const feature = {
            id: row.feature_id,
            name: row.feature_name,
            distance_meters: row.distance_meters,
            ...featureData
          };

          if (row.feature_type === 'highway') {
            highways.push(feature);
          } else if (row.feature_type === 'poi') {
            pois.push(feature);
          }
        });

        // Find the closest named highway (not starting with "other_")
        const namedHighways = highways.filter(h => !h.name.startsWith('other_'));
        const closestNamedHighway = namedHighways.length > 0 
          ? namedHighways.reduce((closest, current) => 
              current.distance_meters < closest.distance_meters ? current : closest
            )
          : null;

        // Find the closest POI
        const closestPoi = pois.length > 0
          ? pois.reduce((closest, current) => 
              current.distance_meters < closest.distance_meters ? current : closest
            )
          : null;

        return {
          location: { latitude, longitude },
          search_radius_meters: distanceMeters,
          closest_named_highway: closestNamedHighway,
          closest_poi: closestPoi,
          nearby_highways: highways,
          nearby_pois: pois,
          total_count: highways.length + pois.length
        };
      } catch (error) {
        strapi.log.error('Error finding nearby features:', error);
        return ctx.badRequest('Error finding nearby features');
      }
    }

    // Otherwise, use default find behavior
    return super.find(ctx);
  }
}));
