"use strict";
/**
 * Active Passenger API Routes
 * Provides CRUD + spatial query endpoints for real-time passenger data
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    routes: [
        // Standard CRUD routes
        {
            method: 'GET',
            path: '/active-passengers',
            handler: 'active-passenger.find',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/active-passengers/:id',
            handler: 'active-passenger.findOne',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'POST',
            path: '/active-passengers',
            handler: 'active-passenger.create',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'PUT',
            path: '/active-passengers/:id',
            handler: 'active-passenger.update',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'DELETE',
            path: '/active-passengers/:id',
            handler: 'active-passenger.delete',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        // Custom routes for passenger operations
        {
            method: 'POST',
            path: '/active-passengers/mark-boarded/:passengerId',
            handler: 'active-passenger.markBoarded',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'POST',
            path: '/active-passengers/mark-alighted/:passengerId',
            handler: 'active-passenger.markAlighted',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/active-passengers/near-location',
            handler: 'active-passenger.findNearLocation',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/active-passengers/by-route/:routeId',
            handler: 'active-passenger.findByRoute',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/active-passengers/by-status/:status',
            handler: 'active-passenger.findByStatus',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'DELETE',
            path: '/active-passengers/cleanup/expired',
            handler: 'active-passenger.deleteExpired',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/active-passengers/stats/count',
            handler: 'active-passenger.getCount',
            config: {
                policies: [],
                middlewares: [],
            },
        },
    ],
};
//# sourceMappingURL=active-passenger.js.map