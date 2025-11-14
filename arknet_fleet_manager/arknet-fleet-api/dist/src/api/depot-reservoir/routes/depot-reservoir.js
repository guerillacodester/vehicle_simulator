"use strict";
/**
 * Depot Reservoir API Routes - TypeScript
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    routes: [
        {
            method: 'POST',
            path: '/depot-reservoir/spawn-batch',
            handler: 'depot-reservoir.spawnBatch',
            config: {
                policies: [],
                middlewares: [],
            },
        },
        {
            method: 'GET',
            path: '/depot-reservoir/status/:depotId',
            handler: 'depot-reservoir.getStatus',
            config: {
                policies: [],
                middlewares: [],
            },
        },
    ],
};
//# sourceMappingURL=depot-reservoir.js.map