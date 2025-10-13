export default {
  /**
   * Cascade delete: When a GeoJSON file is deleted, also delete all related geographic data
   */
  async beforeDelete(event: any) {
    const fileId = event.params.where.id;
    
    try {
      // Find which country uses this file
      const countries = await strapi.entityService.findMany('api::country.country' as any, {
        filters: {
          $or: [
            { pois_geojson_file: { id: fileId } },
            { place_names_geojson_file: { id: fileId } },
            { landuse_geojson_file: { id: fileId } },
            { regions_geojson_file: { id: fileId } }
          ]
        } as any,
        populate: ['pois_geojson_file', 'place_names_geojson_file', 'landuse_geojson_file', 'regions_geojson_file']
      }) as any[];
      
      if (countries.length === 0) {
        console.log(`[File Delete] File ${fileId} is not a GeoJSON file used by any country`);
        return;
      }
      
      for (const country of countries) {
        console.log(`[File Delete] File ${fileId} belongs to country: ${country.name}`);
        
        // Check which type of file is being deleted
        if (country.pois_geojson_file?.id === fileId) {
          console.log('[File Delete] Deleting all POIs for this country...');
          const deletedCount = await strapi.db.query('api::poi.poi').deleteMany({
            where: { country: country.id }
          });
          console.log(`[File Delete] ✅ Deleted ${deletedCount} POIs for ${country.name}`);
        }
        
        if (country.place_names_geojson_file?.id === fileId) {
          console.log('[File Delete] Deleting all Places for this country...');
          const deletedCount = await strapi.db.query('api::place.place').deleteMany({
            where: { country: country.id }
          });
          console.log(`[File Delete] ✅ Deleted ${deletedCount} Places for ${country.name}`);
        }
        
        if (country.landuse_geojson_file?.id === fileId) {
          console.log('[File Delete] Deleting all Landuse zones for this country...');
          const deletedCount = await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
            where: { country: country.id }
          });
          console.log(`[File Delete] ✅ Deleted ${deletedCount} Landuse zones for ${country.name}`);
        }
        
        if (country.regions_geojson_file?.id === fileId) {
          console.log('[File Delete] Deleting all Regions for this country...');
          const regions = await strapi.entityService.findMany('api::region.region' as any, {
            filters: { country: country.id }
          }) as any[];
          
          for (const region of regions) {
            await strapi.entityService.delete('api::region.region' as any, region.id);
          }
          console.log(`[File Delete] ✅ Deleted ${regions.length} Regions for ${country.name}`);
        }
      }
      
    } catch (error) {
      console.error('[File Delete] Error during cascade delete:', error);
    }
  }
};
