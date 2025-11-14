"use strict";
/**
 * Passenger Spawning API Routes - TypeScript
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    routes: [
        {
            method: 'POST',
            path: '/passenger-spawning/generate',
            handler: 'passenger-spawning.generate',
            config: {
                policies: [],
                middlewares: [],
            },
        },
    ],
};
//# sourceMappingURL=passenger-spawning.js.map