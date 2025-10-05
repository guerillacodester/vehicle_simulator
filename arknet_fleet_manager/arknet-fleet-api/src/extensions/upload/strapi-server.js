const _ = require('lodash');

module.exports = (plugin) => {
  console.log('[Upload Plugin Extension] Configuring GeoJSON support...');
  
  // Override the upload configuration to add GeoJSON MIME types
  const originalConfig = plugin.config;
  plugin.config = _.merge({}, originalConfig, {
    breakpoints: {
      xlarge: 1920,
      large: 1000,
      medium: 750,
      small: 500,
      xsmall: 64
    },
    // Add GeoJSON-specific configuration
    sizeLimit: 200 * 1024 * 1024, // 200MB
  });
  
  // Override the file validation service
  const originalIsValidFileType = plugin.services.upload.isValidFileType;
  
  plugin.services.upload.isValidFileType = function(file, allowedTypes) {
    console.log(`[Upload Override] Checking file: ${file.name}, MIME: ${file.type || file.mime}`);
    console.log(`[Upload Override] Allowed types: ${JSON.stringify(allowedTypes)}`);
    
    // If allowedTypes includes 'files', accept GeoJSON
    if (allowedTypes && allowedTypes.includes('files')) {
      // Allow .geojson and .json files
      if (file.name) {
        const ext = file.name.toLowerCase();
        if (ext.endsWith('.geojson') || ext.endsWith('.json')) {
          console.log('[Upload Override] ✅ Accepting GeoJSON/JSON file');
          return true;
        }
      }
      
      // Allow JSON MIME types
      const jsonMimeTypes = [
        'application/json',
        'application/geo+json',
        'application/vnd.geo+json',
        'text/plain',
        'text/json'
      ];
      
      const fileMime = file.type || file.mime;
      if (fileMime && jsonMimeTypes.includes(fileMime)) {
        console.log(`[Upload Override] ✅ Accepting JSON MIME type: ${fileMime}`);
        return true;
      }
    }
    
    // Fall back to original validation
    const result = originalIsValidFileType.call(this, file, allowedTypes);
    console.log(`[Upload Override] Original validation result: ${result}`);
    return result;
  };
  
  // Add cascade delete when file is removed
  const originalRemove = plugin.services.upload.remove;
  plugin.services.upload.remove = async function(file) {
    console.log(`[File Delete Service] Deleting file ID: ${file.id}, name: ${file.name}`);
    
    try {
      // Find which country uses this file
      const countries = await strapi.entityService.findMany('api::country.country', {
        filters: {
          $or: [
            { pois_geojson_file: file.id },
            { place_names_geojson_file: file.id },
            { landuse_geojson_file: file.id },
            { regions_geojson_file: file.id }
          ]
        },
        populate: ['pois_geojson_file', 'place_names_geojson_file', 'landuse_geojson_file', 'regions_geojson_file']
      });
      
      if (countries.length === 0) {
        console.log(`[File Delete Service] File ${file.id} is not a GeoJSON file used by any country`);
      } else {
        for (const country of countries) {
          console.log(`[File Delete Service] File ${file.id} belongs to country: ${country.name}`);
          
          // Check which type of file is being deleted
          if (country.pois_geojson_file?.id === file.id) {
            console.log('[File Delete Service] Deleting all POIs for this country...');
            const deletedCount = await strapi.db.query('api::poi.poi').deleteMany({
              where: { country: country.id }
            });
            console.log(`[File Delete Service] ✅ Deleted ${deletedCount} POIs for ${country.name}`);
          }
          
          if (country.place_names_geojson_file?.id === file.id) {
            console.log('[File Delete Service] Deleting all Places for this country...');
            const deletedCount = await strapi.db.query('api::place.place').deleteMany({
              where: { country: country.id }
            });
            console.log(`[File Delete Service] ✅ Deleted ${deletedCount} Places for ${country.name}`);
          }
          
          if (country.landuse_geojson_file?.id === file.id) {
            console.log('[File Delete Service] Deleting all Landuse zones for this country...');
            const deletedCount = await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
              where: { country: country.id }
            });
            console.log(`[File Delete Service] ✅ Deleted ${deletedCount} Landuse zones for ${country.name}`);
          }
          
          if (country.regions_geojson_file?.id === file.id) {
            console.log('[File Delete Service] Deleting all Regions for this country...');
            const regions = await strapi.entityService.findMany('api::region.region', {
              filters: { country: country.id }
            });
            
            for (const region of regions) {
              await strapi.entityService.delete('api::region.region', region.id);
            }
            console.log(`[File Delete Service] ✅ Deleted ${regions.length} Regions for ${country.name}`);
          }
        }
      }
    } catch (error) {
      console.error('[File Delete Service] Error during cascade delete:', error);
    }
    
    // Call the original remove method
    return originalRemove.call(this, file);
  };
  
  // Also override the controller's remove action
  const originalControllerRemove = plugin.controllers.upload.remove;
  plugin.controllers.upload.remove = async function(ctx) {
    const { id } = ctx.params;
    console.log(`[File Delete Controller] File ID: ${id} deletion requested`);
    
    // Get the file first
    const file = await strapi.plugin('upload').service('upload').findOne(id);
    
    if (file) {
      console.log(`[File Delete Controller] Found file: ${file.name}, triggering cascade delete...`);
      
      try {
        // Find which country uses this file
        const countries = await strapi.entityService.findMany('api::country.country', {
          filters: {
            $or: [
              { pois_geojson_file: file.id },
              { place_names_geojson_file: file.id },
              { landuse_geojson_file: file.id },
              { regions_geojson_file: file.id }
            ]
          },
          populate: ['pois_geojson_file', 'place_names_geojson_file', 'landuse_geojson_file', 'regions_geojson_file']
        });
        
        if (countries.length > 0) {
          for (const country of countries) {
            console.log(`[File Delete Controller] File ${file.id} belongs to country: ${country.name}`);
            
            // Check which type of file is being deleted
            if (country.pois_geojson_file?.id === file.id) {
              console.log('[File Delete Controller] Deleting all POIs for this country...');
              const deletedCount = await strapi.db.query('api::poi.poi').deleteMany({
                where: { country: country.id }
              });
              console.log(`[File Delete Controller] ✅ Deleted ${deletedCount} POIs for ${country.name}`);
            }
            
            if (country.place_names_geojson_file?.id === file.id) {
              console.log('[File Delete Controller] Deleting all Places for this country...');
              const deletedCount = await strapi.db.query('api::place.place').deleteMany({
                where: { country: country.id }
              });
              console.log(`[File Delete Controller] ✅ Deleted ${deletedCount} Places for ${country.name}`);
            }
            
            if (country.landuse_geojson_file?.id === file.id) {
              console.log('[File Delete Controller] Deleting all Landuse zones for this country...');
              const deletedCount = await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
                where: { country: country.id }
              });
              console.log(`[File Delete Controller] ✅ Deleted ${deletedCount} Landuse zones for ${country.name}`);
            }
            
            if (country.regions_geojson_file?.id === file.id) {
              console.log('[File Delete Controller] Deleting all Regions for this country...');
              const regions = await strapi.entityService.findMany('api::region.region', {
                filters: { country: country.id }
              });
              
              for (const region of regions) {
                await strapi.entityService.delete('api::region.region', region.id);
              }
              console.log(`[File Delete Controller] ✅ Deleted ${regions.length} Regions for ${country.name}`);
            }
          }
        }
      } catch (error) {
        console.error('[File Delete Controller] Error during cascade delete:', error);
      }
    }
    
    // Call the original controller method
    return originalControllerRemove.call(this, ctx);
  };
  
  console.log('[Upload Plugin Extension] ✅ GeoJSON support configured');
  
  return plugin;
};