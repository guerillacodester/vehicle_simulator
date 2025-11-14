"use strict";
/**
 * 🚨 CRITICAL WARNING - READ BEFORE EDITING 🚨
 * ============================================
 * The database route_shapes + shapes tables are FRAGMENTED!
 * - Route 1 has 27 separate shape segments with NO ORDERING
 * - Concatenating all shapes gives 91km of random jumps (WRONG)
 * - Default shape is only 1.3km (one segment, WRONG)
 *
 * THE SINGLE SOURCE OF TRUTH:
 * - GeoJSON files: arknet_transit_simulator/data/route_*.geojson
 * - Route 1: 415 coordinates, 27 ordered segments, 13.347 km
 *
 * 📖 READ: /ROUTE_GEOMETRY_BIBLE.md
 *
 * TODO: Proxy to GeoJSON files, NOT database fragments
 */
Object.defineProperty(exports, "__esModule", { value: true });
const strapi_1 = require("@strapi/strapi");
exports.default = strapi_1.factories.createCoreController('api::route.route', ({ strapi }) => ({
    // Override find to return list with basic info
    async find(ctx) {
        const { data, meta } = await super.find(ctx);
        // Transform to simple format for list view (defensive)
        const routes = (data || []).map((item) => {
            const attrs = (item && item.attributes) || {};
            const parishes = attrs.parishes || '';
            const parts = String(parishes).split(',');
            return {
                id: item && item.id,
                attributes: {
                    code: attrs.short_name || attrs.code || '',
                    name: attrs.long_name || attrs.short_name || attrs.name || '',
                    origin: (parts[0] || '').trim(),
                    destination: (parts[1] || '').trim(),
                    color: attrs.color || ''
                }
            };
        });
        return { data: routes, meta };
    },
    // Override findOne to include GTFS-compliant stops and shapes
    async findOne(ctx) {
        var _a, _b, _c, _d, _e;
        const { id } = ctx.params;
        // Get route
        const route = await strapi.entityService.findOne('api::route.route', id, {
            populate: ['trips']
        });
        if (!route) {
            return ctx.notFound('Route not found');
        }
        // Use short_name as route_id for route_shapes lookup
        const routeId = route.short_name || String(route.id);
        let stops = [];
        let shapePoints = [];
        // Find DEFAULT route_shape for this route (NOT all variants!)
        const routeShapes = await strapi.entityService.findMany('api::route-shape.route-shape', {
            filters: {
                route_id: routeId,
                is_default: true // ONLY get the default shape
            }
        });
        if (routeShapes && routeShapes.length > 0) {
            // Get the default shape_id
            const defaultShapeId = routeShapes[0].shape_id;
            // Get shape points for ONLY the default shape
            const shapes = await strapi.entityService.findMany('api::shape.shape', {
                filters: { shape_id: defaultShapeId },
                sort: ['shape_pt_sequence:asc'],
                pagination: { pageSize: 10000 }
            });
            shapePoints = shapes.map((s) => [
                parseFloat(s.shape_pt_lon),
                parseFloat(s.shape_pt_lat)
            ]);
        }
        // Get stops from trips if available
        const trips = route.trips || [];
        const representativeTripId = (_a = trips.find((t) => t.id)) === null || _a === void 0 ? void 0 : _a.id;
        if (representativeTripId) {
            const stopTimes = await strapi.entityService.findMany('api::stop-time.stop-time', {
                filters: { trip: representativeTripId },
                populate: ['stop'],
                sort: ['stop_sequence:asc']
            });
            stops = stopTimes.map((st) => {
                var _a, _b, _c, _d, _e;
                return ({
                    id: ((_a = st.stop) === null || _a === void 0 ? void 0 : _a.stop_id) || ((_b = st.stop) === null || _b === void 0 ? void 0 : _b.id),
                    name: ((_c = st.stop) === null || _c === void 0 ? void 0 : _c.name) || '',
                    lat: parseFloat(((_d = st.stop) === null || _d === void 0 ? void 0 : _d.latitude) || 0),
                    lon: parseFloat(((_e = st.stop) === null || _e === void 0 ? void 0 : _e.longitude) || 0),
                    sequence: st.stop_sequence
                });
            });
        }
        return {
            data: {
                id: route.id,
                attributes: {
                    code: route.short_name,
                    name: route.long_name || route.short_name,
                    origin: ((_c = (_b = route.parishes) === null || _b === void 0 ? void 0 : _b.split(',')[0]) === null || _c === void 0 ? void 0 : _c.trim()) || '',
                    destination: ((_e = (_d = route.parishes) === null || _d === void 0 ? void 0 : _d.split(',')[1]) === null || _e === void 0 ? void 0 : _e.trim()) || '',
                    color: route.color,
                    stops: stops,
                    geometry: shapePoints.length > 0 ? {
                        type: 'LineString',
                        coordinates: shapePoints,
                        distanceKm: shapePoints.length > 1 ? shapePoints.reduce((acc, curr, idx, arr) => {
                            if (idx === 0)
                                return 0;
                            const [lon1, lat1] = arr[idx - 1];
                            const [lon2, lat2] = curr;
                            const R = 6371.0;
                            const toRad = (v) => (v * Math.PI) / 180.0;
                            const dLat = toRad(lat2 - lat1);
                            const dLon = toRad(lon2 - lon1);
                            const lat1r = toRad(lat1);
                            const lat2r = toRad(lat2);
                            const s = Math.sin(dLat / 2) ** 2 + Math.cos(lat1r) * Math.cos(lat2r) * Math.sin(dLon / 2) ** 2;
                            const c = 2 * Math.atan2(Math.sqrt(s), Math.sqrt(1 - s));
                            return acc + R * c;
                        }, 0) : 0
                    } : null
                }
            }
        };
    },
    // Get route geometry with distance calculation
    async getGeometry(ctx) {
        const { routeName } = ctx.params;
        try {
            const result = await strapi.service('api::route.route').fetchRouteGeometry(routeName);
            ctx.body = {
                success: true,
                routeName,
                metrics: result.metrics,
                coordinateCount: result.coords.length,
                segmentCount: result.segments.length,
                coordinates: result.coords,
                distanceKm: Number(result.metrics.estimatedLengthKm),
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : 'Unknown error',
            };
        }
    }
}));
//# sourceMappingURL=route.js.map