"use strict";
/**
 * Active Passenger Controller
 * Handles passenger lifecycle and spatial queries
 */
Object.defineProperty(exports, "__esModule", { value: true });
const strapi_1 = require("@strapi/strapi");
exports.default = strapi_1.factories.createCoreController('api::active-passenger.active-passenger', ({ strapi }) => ({
    /**
     * Mark a passenger as boarded (status = ONBOARD)
     */
    async markBoarded(ctx) {
        try {
            const { passengerId } = ctx.params;
            // Find passenger by passenger_id field (not database ID)
            const passengers = await strapi.entityService.findMany('api::active-passenger.active-passenger', {
                filters: { passenger_id: passengerId },
                limit: 1,
            });
            if (!passengers || passengers.length === 0) {
                ctx.status = 404;
                return { error: `Passenger ${passengerId} not found` };
            }
            const passenger = passengers[0];
            // Update status and boarded_at timestamp
            const updated = await strapi.entityService.update('api::active-passenger.active-passenger', passenger.id, {
                data: {
                    status: 'ONBOARD',
                    boarded_at: new Date(),
                },
            });
            ctx.body = {
                success: true,
                passenger_id: passengerId,
                status: 'ONBOARD',
                boarded_at: updated.boarded_at,
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
    /**
     * Mark a passenger as alighted (status = COMPLETED)
     */
    async markAlighted(ctx) {
        try {
            const { passengerId } = ctx.params;
            // Find passenger by passenger_id field
            const passengers = await strapi.entityService.findMany('api::active-passenger.active-passenger', {
                filters: { passenger_id: passengerId },
                limit: 1,
            });
            if (!passengers || passengers.length === 0) {
                ctx.status = 404;
                return { error: `Passenger ${passengerId} not found` };
            }
            const passenger = passengers[0];
            // Update status and alighted_at timestamp
            const updated = await strapi.entityService.update('api::active-passenger.active-passenger', passenger.id, {
                data: {
                    status: 'COMPLETED',
                    alighted_at: new Date(),
                },
            });
            ctx.body = {
                success: true,
                passenger_id: passengerId,
                status: 'COMPLETED',
                alighted_at: updated.alighted_at,
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
    /**
     * Find passengers near a location using distance calculation
     * Query params: lat, lon, radius (meters), route_id (optional), status (optional)
     */
    async findNearLocation(ctx) {
        try {
            const { lat, lon, radius = 500, route_id, status = 'WAITING' } = ctx.query;
            if (!lat || !lon) {
                ctx.status = 400;
                return { error: 'lat and lon query parameters are required' };
            }
            const latitude = parseFloat(lat);
            const longitude = parseFloat(lon);
            const radiusMeters = parseFloat(radius);
            // Build filters
            const filters = {
                status: status,
            };
            if (route_id) {
                filters.route_id = route_id;
            }
            // Get all passengers matching filters
            const passengers = await strapi.entityService.findMany('api::active-passenger.active-passenger', {
                filters,
            });
            // Calculate distances and filter by radius
            const passengersWithDistance = passengers
                .map((p) => ({
                ...p,
                distance_meters: calculateDistance(latitude, longitude, p.latitude, p.longitude),
            }))
                .filter((p) => p.distance_meters <= radiusMeters)
                .sort((a, b) => a.distance_meters - b.distance_meters);
            ctx.body = {
                success: true,
                count: passengersWithDistance.length,
                center: { latitude, longitude },
                radius_meters: radiusMeters,
                passengers: passengersWithDistance,
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
    /**
     * Find passengers by route ID
     */
    async findByRoute(ctx) {
        try {
            const { routeId } = ctx.params;
            const { status } = ctx.query;
            const filters = { route_id: routeId };
            if (status) {
                filters.status = status;
            }
            const passengers = await strapi.entityService.findMany('api::active-passenger.active-passenger', {
                filters,
            });
            ctx.body = {
                success: true,
                route_id: routeId,
                count: passengers.length,
                passengers,
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
    /**
     * Find passengers by status
     */
    async findByStatus(ctx) {
        try {
            const { status } = ctx.params;
            const passengers = await strapi.entityService.findMany('api::active-passenger.active-passenger', {
                filters: { status },
            });
            ctx.body = {
                success: true,
                status,
                count: passengers.length,
                passengers,
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
    /**
     * Delete expired passengers (expires_at < now AND status = WAITING)
     */
    async deleteExpired(ctx) {
        try {
            const now = new Date();
            // Find expired passengers
            const expiredPassengers = await strapi.db
                .query('api::active-passenger.active-passenger')
                .findMany({
                where: {
                    status: 'WAITING',
                    expires_at: {
                        $lt: now,
                    },
                },
            });
            // Delete them
            const deletePromises = expiredPassengers.map((p) => strapi.entityService.delete('api::active-passenger.active-passenger', p.id));
            await Promise.all(deletePromises);
            ctx.body = {
                success: true,
                deleted_count: expiredPassengers.length,
                deleted_passenger_ids: expiredPassengers.map((p) => p.passenger_id),
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
    /**
     * Get passenger count statistics
     * Query params: route_id (optional), status (optional)
     */
    async getCount(ctx) {
        try {
            const { route_id, status } = ctx.query;
            const filters = {};
            if (route_id)
                filters.route_id = route_id;
            if (status)
                filters.status = status;
            const passengers = await strapi.entityService.findMany('api::active-passenger.active-passenger', {
                filters,
            });
            // Count by status
            const statusCounts = {};
            passengers.forEach((p) => {
                statusCounts[p.status] = (statusCounts[p.status] || 0) + 1;
            });
            ctx.body = {
                success: true,
                total: passengers.length,
                filters: { route_id, status },
                by_status: statusCounts,
            };
        }
        catch (error) {
            ctx.status = 500;
            ctx.body = {
                success: false,
                error: error instanceof Error ? error.message : String(error),
            };
        }
    },
}));
/**
 * Calculate distance between two lat/lon points using Haversine formula
 * Returns distance in meters
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371e3; // Earth radius in meters
    const φ1 = (lat1 * Math.PI) / 180;
    const φ2 = (lat2 * Math.PI) / 180;
    const Δφ = ((lat2 - lat1) * Math.PI) / 180;
    const Δλ = ((lon2 - lon1) * Math.PI) / 180;
    const a = Math.sin(Δφ / 2) * Math.sin(Δφ / 2) +
        Math.cos(φ1) * Math.cos(φ2) * Math.sin(Δλ / 2) * Math.sin(Δλ / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}
//# sourceMappingURL=active-passenger.js.map