"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const strapi_1 = require("@strapi/strapi");
exports.default = strapi_1.factories.createCoreController('api::geofence.geofence', ({ strapi }) => ({
    /**
     * Override find method to add nearby highways and POIs when lat/lon is provided
     */
    async find(ctx) {
        const { lat, lon, distance = 50 } = ctx.query;
        // If lat/lon provided, find nearby highways and POIs
        if (lat && lon) {
            try {
                const latitude = parseFloat(lat);
                const longitude = parseFloat(lon);
                const distanceMeters = parseFloat(distance);
                if (isNaN(latitude) || isNaN(longitude) || isNaN(distanceMeters)) {
                    return ctx.badRequest('Invalid parameters: lat, lon, and distance must be valid numbers');
                }
                // Query the database directly using plain SQL (optimized version)
                const query = `
          SELECT * FROM find_nearby_features_fast(${latitude}, ${longitude}, ${distanceMeters})
        `;
                const result = await strapi.db.connection.raw(query);
                const rows = result.rows || result[0] || [];
                // Group results by feature type
                const highways = [];
                const pois = [];
                rows.forEach((row) => {
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
                    }
                    else if (row.feature_type === 'poi') {
                        pois.push(feature);
                    }
                });
                // Find the closest named highway (not starting with "other_")
                const namedHighways = highways.filter(h => !h.name.startsWith('other_'));
                let closestNamedHighway = namedHighways.length > 0
                    ? namedHighways.reduce((closest, current) => current.distance_meters < closest.distance_meters ? current : closest)
                    : null;
                // Find the closest POI
                let closestPoi = pois.length > 0
                    ? pois.reduce((closest, current) => current.distance_meters < closest.distance_meters ? current : closest)
                    : null;
                // If either feature is missing, do ONE expanded search (500m) for both
                if (!closestNamedHighway || !closestPoi) {
                    const expandedQuery = `
            SELECT * FROM find_nearby_features_fast(${latitude}, ${longitude}, 500)
          `;
                    const expandedResult = await strapi.db.connection.raw(expandedQuery);
                    const expandedRows = expandedResult.rows || expandedResult[0] || [];
                    if (!closestNamedHighway) {
                        const expandedHighways = expandedRows
                            .filter((row) => row.feature_type === 'highway')
                            .map((row) => ({
                            name: row.feature_name,
                            distance_meters: row.distance_meters
                        }))
                            .filter((h) => !h.name.startsWith('other_'));
                        if (expandedHighways.length > 0) {
                            closestNamedHighway = expandedHighways.reduce((closest, current) => current.distance_meters < closest.distance_meters ? current : closest);
                        }
                    }
                    if (!closestPoi) {
                        const expandedPois = expandedRows
                            .filter((row) => row.feature_type === 'poi')
                            .map((row) => ({
                            name: row.feature_name,
                            distance_meters: row.distance_meters
                        }));
                        if (expandedPois.length > 0) {
                            closestPoi = expandedPois.reduce((closest, current) => current.distance_meters < closest.distance_meters ? current : closest);
                        }
                    }
                }
                return {
                    latitude,
                    longitude,
                    highway: closestNamedHighway ? {
                        name: closestNamedHighway.name,
                        distance_meters: closestNamedHighway.distance_meters
                    } : null,
                    poi: closestPoi ? {
                        name: closestPoi.name,
                        distance_meters: closestPoi.distance_meters
                    } : null
                };
            }
            catch (error) {
                strapi.log.error('Error finding nearby features:', error);
                return ctx.badRequest('Error finding nearby features');
            }
        }
        // Otherwise, use default find behavior
        return super.find(ctx);
    }
}));
//# sourceMappingURL=geofence.js.map