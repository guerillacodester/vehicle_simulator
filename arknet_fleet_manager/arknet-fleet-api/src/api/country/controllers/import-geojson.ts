/**
 * Direct GeoJSON import controller
 * Reads GeoJSON files from disk and imports them into the database
 * No upload needed - just specify the file path
 */

import { factories } from '@strapi/strapi';
import fs from 'fs/promises';
import path from 'path';

export default factories.createCoreController('api::country.country', ({ strapi }) => ({
  /**
   * Import GeoJSON from local file path
   * POST /api/countries/:id/import-geojson
   * Body: { 
   *   type: 'pois' | 'landuse' | 'regions' | 'highways',
   *   filePath: 'E:/projects/github/vehicle_simulator/sample_data/amenity.geojson'
   * }
   */
  async importFromFile(ctx) {
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
      const fileContent = await fs.readFile(filePath, 'utf-8');
      const geojsonData = JSON.parse(fileContent);

      // Get the country
      const country = await strapi.entityService.findOne('api::country.country', id);
      if (!country) {
        return ctx.notFound('Country not found');
      }

      console.log(`[Import] Starting ${type} import for ${country.name} from ${filePath}`);
      console.log(`[Import] Features to import: ${geojsonData.features?.length || 0}`);

      // Update country with GeoJSON data
      const fieldMap: Record<string, string> = {
        pois: 'pois_geojson_data',
        landuse: 'landuse_geojson_data',
        regions: 'regions_geojson_data',
        highways: 'highways_geojson_data',
      };

      const updateData: any = {
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
          message: `${type} GeoJSON data stored from ${path.basename(filePath)}`,
          featureCount: geojsonData.features?.length || 0,
          note: 'Data stored - processing must be triggered separately',
        },
      });

    } catch (error: any) {
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
      console.log(`[Import] Features to import: ${geojsonData.features?.length || 0}`);

      // Update country with GeoJSON data
      const fieldMap: Record<string, string> = {
        pois: 'pois_geojson_data',
        landuse: 'landuse_geojson_data',
        regions: 'regions_geojson_data',
        highways: 'highways_geojson_data',
      };

      const updateData: any = {
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
          featureCount: geojsonData.features?.length || 0,
          note: 'Data stored - processing must be triggered separately',
        },
      });

    } catch (error: any) {
      console.error(`[Import] Error importing ${type}:`, error);
      return ctx.internalServerError(`Import failed: ${error.message}`);
    }
  },
}));
