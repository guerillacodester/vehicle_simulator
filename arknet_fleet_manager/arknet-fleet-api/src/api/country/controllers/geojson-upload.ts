/**
 * Custom GeoJSON Upload Controller
 * Direct upload endpoint that bypasses Strapi's media library restrictions
 */

export default {
  async uploadGeoJSON(ctx: any) {
    try {
      const { files } = ctx.request;
      const { countryId, fileType } = ctx.request.body;

      if (!files || !files.geojson) {
        return ctx.badRequest('No GeoJSON file provided');
      }

      if (!countryId) {
        return ctx.badRequest('Country ID is required');
      }

      if (!fileType || !['pois', 'places', 'landuse', 'regions'].includes(fileType)) {
        return ctx.badRequest('Invalid file type. Must be: pois, places, landuse, or regions');
      }

      const file = files.geojson;
      
      // Validate it's a JSON file
      if (!file.name.endsWith('.json') && !file.name.endsWith('.geojson')) {
        return ctx.badRequest('File must be .json or .geojson');
      }

      // Read and parse the GeoJSON
      const fs = require('fs');
      const fileContent = fs.readFileSync(file.path, 'utf-8');
      const geoJSON = JSON.parse(fileContent);

      if (!geoJSON.type || !geoJSON.features) {
        return ctx.badRequest('Invalid GeoJSON format');
      }

      // Upload to Strapi's upload plugin
      const uploadService = strapi.plugin('upload').service('upload');
      
      const uploadedFile = await uploadService.upload({
        data: {
          fileInfo: {
            name: file.name,
            caption: `${fileType} GeoJSON for country ${countryId}`,
            alternativeText: file.name,
          },
        },
        files: file,
      });

      // Update the country record with the uploaded file
      const fieldMap: any = {
        pois: 'pois_geojson_file',
        places: 'place_names_geojson_file',
        landuse: 'landuse_geojson_file',
        regions: 'regions_geojson_file',
      };

      const country = await strapi.entityService.update(
        'api::country.country',
        countryId,
        {
          data: {
            [fieldMap[fileType]]: uploadedFile[0].id,
          },
        }
      );

      return ctx.send({
        success: true,
        message: `GeoJSON file uploaded successfully`,
        file: uploadedFile[0],
        country: country,
        features: geoJSON.features.length,
      });

    } catch (error: any) {
      console.error('[GeoJSON Upload] Error:', error);
      return ctx.badRequest(error.message);
    }
  },
};
