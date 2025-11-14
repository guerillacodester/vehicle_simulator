"use strict";
/**
 * Direct GeoJSON import controller
 * Reads GeoJSON files from disk and imports them into the database
 * No upload needed - just specify the file path
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const strapi_1 = require("@strapi/strapi");
const promises_1 = __importDefault(require("fs/promises"));
const path_1 = __importDefault(require("path"));
exports.default = strapi_1.factories.createCoreController('api::country.country', ({ strapi }) => ({
    /**
     * Import GeoJSON from local file path
     * POST /api/countries/:id/import-geojson
     * Body: {
     *   type: 'pois' | 'landuse' | 'regions' | 'highways',
     *   filePath: 'E:/projects/github/vehicle_simulator/sample_data/amenity.geojson'
     * }
     */
    async importFromFile(ctx) {
        var _a, _b;
        const { id } = ctx.params;
        const { type, filePath } = ctx.request.body;
        if (!type || !filePath) {
            return ctx.badRequest('Missing type or filePath');
        }
        if (!['pois', 'landuse', 'regions', 'highways'].includes(type)) {
            return ctx.badRequest('Invalid type. Must be: pois, landuse, regions, or highways');
        }
        try {
            // Read GeoJSON file from disk
            const fileContent = await promises_1.default.readFile(filePath, 'utf-8');
            const geojsonData = JSON.parse(fileContent);
            // Get the country
            const country = await strapi.entityService.findOne('api::country.country', id);
            if (!country) {
                return ctx.notFound('Country not found');
            }
            console.log(`[Import] Starting ${type} import for ${country.name} from ${filePath}`);
            console.log(`[Import] Features to import: ${((_a = geojsonData.features) === null || _a === void 0 ? void 0 : _a.length) || 0}`);
            // Update country with GeoJSON data
            const fieldMap = {
                pois: 'pois_geojson_data',
                landuse: 'landuse_geojson_data',
                regions: 'regions_geojson_data',
                highways: 'highways_geojson_data',
            };
            const updateData = {
                [fieldMap[type]]: geojsonData,
                geodata_last_import: new Date().toISOString(),
            };
            // Store the GeoJSON data in database
            const updated = await strapi.entityService.update('api::country.country', id, {
                data: updateData,
            });
            console.log(`[Import] ✅ GeoJSON data stored in ${fieldMap[type]}`);
            console.log(`[Import] ⚠️ Note: Automatic processing not yet implemented`);
            console.log(`[Import] You can trigger processing via the lifecycle or manually`);
            return ctx.send({
                success: true,
                data: {
                    message: `${type} GeoJSON data stored from ${path_1.default.basename(filePath)}`,
                    featureCount: ((_b = geojsonData.features) === null || _b === void 0 ? void 0 : _b.length) || 0,
                    note: 'Data stored - processing must be triggered separately',
                },
            });
        }
        catch (error) {
            console.error(`[Import] Error importing ${type}:`, error);
            return ctx.internalServerError(`Import failed: ${error.message}`);
        }
    },
    /**
     * Import GeoJSON from browser-uploaded file content
     * POST /api/countries/:id/import-geojson-direct
     * Body: {
     *   type: 'pois' | 'landuse' | 'regions' | 'highways',
     *   geojsonData: { ... GeoJSON object ... }
     * }
     */
    async importDirect(ctx) {
        var _a, _b;
        const { id } = ctx.params;
        const { type, geojsonData } = ctx.request.body;
        if (!type || !geojsonData) {
            return ctx.badRequest('Missing type or geojsonData');
        }
        if (!['pois', 'landuse', 'regions', 'highways'].includes(type)) {
            return ctx.badRequest('Invalid type. Must be: pois, landuse, regions, or highways');
        }
        try {
            // Get the country
            const country = await strapi.entityService.findOne('api::country.country', id);
            if (!country) {
                return ctx.notFound('Country not found');
            }
            console.log(`[Import] Starting ${type} import for ${country.name}`);
            console.log(`[Import] Features to import: ${((_a = geojsonData.features) === null || _a === void 0 ? void 0 : _a.length) || 0}`);
            // Update country with GeoJSON data
            const fieldMap = {
                pois: 'pois_geojson_data',
                landuse: 'landuse_geojson_data',
                regions: 'regions_geojson_data',
                highways: 'highways_geojson_data',
            };
            const updateData = {
                [fieldMap[type]]: geojsonData,
                geodata_last_import: new Date().toISOString(),
            };
            // Store the GeoJSON data in database
            const updated = await strapi.entityService.update('api::country.country', id, {
                data: updateData,
            });
            console.log(`[Import] ✅ GeoJSON data stored in ${fieldMap[type]}`);
            console.log(`[Import] ⚠️ Note: Automatic processing not yet implemented`);
            console.log(`[Import] You can trigger processing via the lifecycle or manually`);
            return ctx.send({
                success: true,
                data: {
                    message: `${type} GeoJSON data stored successfully`,
                    featureCount: ((_b = geojsonData.features) === null || _b === void 0 ? void 0 : _b.length) || 0,
                    note: 'Data stored - processing must be triggered separately',
                },
            });
        }
        catch (error) {
            console.error(`[Import] Error importing ${type}:`, error);
            return ctx.internalServerError(`Import failed: ${error.message}`);
        }
    },
}));
//# sourceMappingURL=import-geojson.js.map