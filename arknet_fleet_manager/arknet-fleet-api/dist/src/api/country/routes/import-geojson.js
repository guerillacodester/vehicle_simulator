"use strict";
/**
 * Custom routes for direct GeoJSON import from file system
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
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
//# sourceMappingURL=import-geojson.js.map