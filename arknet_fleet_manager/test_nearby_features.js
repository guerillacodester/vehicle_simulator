const knex = require('knex');

const db = knex({
  client: 'pg',
  connection: {
    host: '127.0.0.1',
    port: 5432,
    database: 'arknettransit',
    user: 'david',
    password: 'Ga25w123!'
  }
});

async function testNearbyFeatures() {
  try {
    console.log('Installing find_nearby_features function...\n');
    
    // Read and execute the SQL function
    const fs = require('fs');
    const path = require('path');
    const sqlFile = path.join(__dirname, 'find_nearby_features.sql');
    const sql = fs.readFileSync(sqlFile, 'utf-8');
    
    await db.raw(sql);
    console.log('✅ Function installed successfully\n');
    
    // Test with a point in Barbados (near Bridgetown)
    const testLat = 13.0969;
    const testLon = -59.6145;
    const distance = 50; // meters
    
    console.log(`Testing: Finding features within ${distance}m of (${testLat}, ${testLon})\n`);
    
    const results = await db.raw(`
      SELECT * FROM find_nearby_features(?, ?, ?)
    `, [testLat, testLon, distance]);
    
    console.log(`Found ${results.rows.length} features:\n`);
    
    // Group by type
    const highways = results.rows.filter(r => r.feature_type === 'highway');
    const pois = results.rows.filter(r => r.feature_type === 'poi');
    
    console.log(`Highways: ${highways.length}`);
    highways.forEach(h => {
      console.log(`  - ${h.feature_name || 'Unnamed'} (${h.distance_meters.toFixed(2)}m)`);
      console.log(`    Type: ${h.feature_data.highway_type}, ID: ${h.feature_data.highway_id}`);
    });
    
    console.log(`\nPOIs: ${pois.length}`);
    pois.forEach(p => {
      console.log(`  - ${p.feature_name || 'Unnamed'} (${p.distance_meters.toFixed(2)}m)`);
      console.log(`    Amenity: ${p.feature_data.amenity}, Type: ${p.feature_data.poi_type}`);
    });
    
    // Try a different location with more features (try 100m)
    console.log('\n\n=== Testing with 100m radius ===\n');
    
    const results2 = await db.raw(`
      SELECT * FROM find_nearby_features(?, ?, ?)
    `, [testLat, testLon, 100]);
    
    const highways2 = results2.rows.filter(r => r.feature_type === 'highway');
    const pois2 = results2.rows.filter(r => r.feature_type === 'poi');
    
    console.log(`Found ${results2.rows.length} features (100m radius):`);
    console.log(`  Highways: ${highways2.length}`);
    console.log(`  POIs: ${pois2.length}`);
    
    // Show closest of each type
    if (highways2.length > 0) {
      const closest = highways2[0];
      console.log(`\n  Closest highway: ${closest.feature_name || 'Unnamed'} (${closest.distance_meters.toFixed(2)}m)`);
    }
    
    if (pois2.length > 0) {
      const closest = pois2[0];
      console.log(`  Closest POI: ${closest.feature_name || 'Unnamed'} (${closest.distance_meters.toFixed(2)}m)`);
    }
    
  } catch (error) {
    console.error('Error:', error.message);
    console.error(error);
  } finally {
    await db.destroy();
  }
}

testNearbyFeatures();
