"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    /**
     * Cascade delete: When a GeoJSON file is deleted, also delete all related geographic data
     */
    async beforeDelete(event) {
        var _a, _b, _c, _d;
        const fileId = event.params.where.id;
        try {
            // Find which country uses this file
            const countries = await strapi.entityService.findMany('api::country.country', {
                filters: {
                    $or: [
                        { pois_geojson_file: fileId },
                        { place_names_geojson_file: fileId },
                        { landuse_geojson_file: fileId },
                        { regions_geojson_file: fileId }
                    ]
                },
                populate: ['pois_geojson_file', 'place_names_geojson_file', 'landuse_geojson_file', 'regions_geojson_file']
            });
            if (countries.length === 0) {
                console.log(`[File Delete] File ${fileId} is not a GeoJSON file used by any country`);
                return;
            }
            for (const country of countries) {
                console.log(`[File Delete] File ${fileId} belongs to country: ${country.name}`);
                // Check which type of file is being deleted
                if (((_a = country.pois_geojson_file) === null || _a === void 0 ? void 0 : _a.id) === fileId) {
                    console.log('[File Delete] Deleting all POIs for this country...');
                    const deletedCount = await strapi.db.query('api::poi.poi').deleteMany({
                        where: { country: country.id }
                    });
                    console.log(`[File Delete] ✅ Deleted ${deletedCount} POIs for ${country.name}`);
                }
                if (((_b = country.place_names_geojson_file) === null || _b === void 0 ? void 0 : _b.id) === fileId) {
                    console.log('[File Delete] Deleting all Places for this country...');
                    const deletedCount = await strapi.db.query('api::place.place').deleteMany({
                        where: { country: country.id }
                    });
                    console.log(`[File Delete] ✅ Deleted ${deletedCount} Places for ${country.name}`);
                }
                if (((_c = country.landuse_geojson_file) === null || _c === void 0 ? void 0 : _c.id) === fileId) {
                    console.log('[File Delete] Deleting all Landuse zones for this country...');
                    const deletedCount = await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
                        where: { country: country.id }
                    });
                    console.log(`[File Delete] ✅ Deleted ${deletedCount} Landuse zones for ${country.name}`);
                }
                if (((_d = country.regions_geojson_file) === null || _d === void 0 ? void 0 : _d.id) === fileId) {
                    console.log('[File Delete] Deleting all Regions for this country...');
                    const regions = await strapi.entityService.findMany('api::region.region', {
                        filters: { country: country.id }
                    });
                    for (const region of regions) {
                        await strapi.entityService.delete('api::region.region', region.id);
                    }
                    console.log(`[File Delete] ✅ Deleted ${regions.length} Regions for ${country.name}`);
                }
            }
        }
        catch (error) {
            console.error('[File Delete] Error during cascade delete:', error);
        }
    }
};
//# sourceMappingURL=lifecycles.js.map