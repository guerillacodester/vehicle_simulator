"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    routes: [
        {
            method: 'POST',
            path: '/route-depots/backfill-labels',
            handler: 'route-depot.backfillLabels',
            config: {
                policies: [],
                middlewares: [],
                auth: false,
            },
        },
        {
            method: 'GET',
            path: '/route-depots/debug-columns',
            handler: 'route-depot.debugColumns',
            config: {
                policies: [],
                middlewares: [],
                auth: false,
            },
        },
        {
            method: 'GET',
            path: '/route-depots',
            handler: 'route-depot.find',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/route-depots/:id',
            handler: 'route-depot.findOne',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'POST',
            path: '/route-depots',
            handler: 'route-depot.create',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'PUT',
            path: '/route-depots/:id',
            handler: 'route-depot.update',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'DELETE',
            path: '/route-depots/:id',
            handler: 'route-depot.delete',
            config: {
                policies: [],
                middlewares: [],
            },
        },
    ],
};
//# sourceMappingURL=route-depot.js.map