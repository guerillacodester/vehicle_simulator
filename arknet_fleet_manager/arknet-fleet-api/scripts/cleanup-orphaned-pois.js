/**
 * Cleanup script: Delete all POIs for countries that don't have a POI GeoJSON file attached
 */

const strapi = require('@strapi/strapi')();

async function cleanupOrphanedPOIs() {
  await strapi.load();
  
  console.log('🔍 Finding countries and their POI files...');
  
  // Get all countries with their POI file status
  const countries = await strapi.entityService.findMany('api::country.country', {
    populate: ['pois_geojson_file']
  });
  
  console.log(`\nFound ${countries.length} countries`);
  
  for (const country of countries) {
    console.log(`\n📍 Country: ${country.name}`);
    console.log(`   POI file attached: ${country.pois_geojson_file ? `Yes (ID: ${country.pois_geojson_file.id})` : 'No'}`);
    
    // Count POIs for this country
    const poisCount = await strapi.db.query('api::poi.poi').count({
      where: { country: country.id }
    });
    
    console.log(`   POIs in database: ${poisCount}`);
    
    // If no file attached but POIs exist, delete them
    if (!country.pois_geojson_file && poisCount > 0) {
      console.log(`   ⚠️  Orphaned POIs detected! Deleting ${poisCount} POIs...`);
      
      const deletedCount = await strapi.db.query('api::poi.poi').deleteMany({
        where: { country: country.id }
      });
      
      console.log(`   ✅ Deleted ${deletedCount} orphaned POIs`);
    } else if (country.pois_geojson_file && poisCount === 0) {
      console.log(`   ⚠️  File attached but no POIs - might need re-import`);
    } else if (!country.pois_geojson_file && poisCount === 0) {
      console.log(`   ✓ Clean - no file, no POIs`);
    } else {
      console.log(`   ✓ Normal - file attached with ${poisCount} POIs`);
    }
  }
  
  console.log('\n✅ Cleanup complete!');
  
  await strapi.destroy();
  process.exit(0);
}

cleanupOrphanedPOIs().catch((error) => {
  console.error('❌ Error during cleanup:', error);
  process.exit(1);
});
