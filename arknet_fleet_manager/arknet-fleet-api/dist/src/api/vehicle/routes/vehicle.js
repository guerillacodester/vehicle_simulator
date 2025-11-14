"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    routes: [
        {
            method: 'GET',
            path: '/vehicles',
            handler: 'vehicle.find',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/vehicles/:id',
            handler: 'vehicle.findOne',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'POST',
            path: '/vehicles',
            handler: 'vehicle.create',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'PUT',
            path: '/vehicles/:id',
            handler: 'vehicle.update',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'DELETE',
            path: '/vehicles/:id',
            handler: 'vehicle.delete',
            config: {
                policies: [],
                middlewares: [],
            },
        },
    ],
};
//# sourceMappingURL=vehicle.js.map