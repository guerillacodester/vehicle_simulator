/**
 * Direct GeoJSON Import Script
 * Bypasses media upload - reads files directly from disk
 */

import fs from 'fs';
import path from 'path';

// File paths
const GEOJSON_DIR = path.resolve(__dirname, '../../../commuter_service/geojson_data');
const FILES = {
  pois: 'barbados_amenities.geojson',
  places: 'barbados_names.geojson',
  landuse: 'barbados_landuse.geojson',
  busstops: 'barbados_busstops.geojson'
};

async function importGeoData() {
  console.log('🚀 Starting GeoJSON import...\n');
  
  // Step 1: Get Barbados country record
  console.log('📍 Finding Barbados country record...');
  const countries = await strapi.entityService.findMany('api::country.country' as any, {
    filters: { code: 'BB' } as any
  }) as any[];
  
  if (!countries || countries.length === 0) {
    throw new Error('❌ Barbados country record not found! Create it first.');
  }
  
  const country = countries[0];
  console.log(`✅ Found: ${country.name} (ID: ${country.id})\n`);
  
  // Step 2: Import POIs (Amenities)
  console.log('📥 Importing POIs from barbados_amenities.geojson...');
  const poisFile = path.join(GEOJSON_DIR, FILES.pois);
  
  if (!fs.existsSync(poisFile)) {
    throw new Error(`❌ File not found: ${poisFile}`);
  }
  
  const poisData = JSON.parse(fs.readFileSync(poisFile, 'utf-8'));
  console.log(`📊 Found ${poisData.features.length} POI features`);
  
  // Process in batches of 100
  const BATCH_SIZE = 100;
  let imported = 0;
  
  for (let i = 0; i < poisData.features.length; i += BATCH_SIZE) {
    const batch = poisData.features.slice(i, i + BATCH_SIZE);
    
    for (const feature of batch) {
      try {
        const props = feature.properties;
        const coords = feature.geometry.coordinates;
        
        // Map amenity type
        const amenity = props.amenity?.toLowerCase() || 'other';
        const amenityMap: { [key: string]: string } = {
          'restaurant': 'restaurant',
          'cafe': 'cafe',
          'bar': 'bar',
          'pub': 'bar',
          'fast_food': 'fast_food',
          'bank': 'bank',
          'atm': 'bank',
          'hospital': 'hospital',
          'clinic': 'hospital',
          'pharmacy': 'pharmacy',
          'school': 'school',
          'university': 'school',
          'college': 'school',
          'police': 'police',
          'fire_station': 'fire_station',
          'place_of_worship': 'place_of_worship',
          'fuel': 'fuel',
          'parking': 'parking',
          'post_office': 'post_office',
          'library': 'library',
          'cinema': 'cinema',
          'theatre': 'cinema',
          'hotel': 'hotel',
          'motel': 'hotel',
          'supermarket': 'supermarket',
          'marketplace': 'marketplace',
          'mall': 'shopping_mall',
          'shopping_mall': 'shopping_mall'
        };
        
        const category = amenityMap[amenity] || 'other';
        
        // Calculate spawn weight
        const highValueTypes = ['restaurant', 'cafe', 'bar', 'supermarket', 'bank', 'hospital'];
        const spawnWeight = highValueTypes.includes(category) ? 10.0 : 5.0;
        
        await strapi.entityService.create('api::poi.poi' as any, {
          data: {
            osm_id: props.osm_id?.toString() || `poi_${i}`,
            name: props.name || `POI ${i}`,
            amenity_type: category,
            coordinates: {
              type: 'Point',
              coordinates: coords
            },
            spawn_weight: spawnWeight,
            country: country.id,
            publishedAt: new Date()
          }
        });
        
        imported++;
      } catch (error: any) {
        console.error(`⚠️  Failed to import POI: ${error.message}`);
      }
    }
    
    console.log(`  ✅ Batch ${Math.floor(i / BATCH_SIZE) + 1}: ${batch.length} POIs processed (${imported} total)`);
  }
  
  console.log(`\n🎉 Import complete! ${imported} POIs imported successfully.`);
}

// Bootstrap Strapi and run import
async function main() {
  try {
    // @ts-ignore - Strapi bootstrap
    await strapi.load();
    await importGeoData();
    process.exit(0);
  } catch (error: any) {
    console.error('💥 Import failed:', error.message);
    process.exit(1);
  }
}

main();
