const knex = require('knex');

async function cleanup() {
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

  try {
    const countryId = 29; // Barbados
    
    console.log('Counting current records...');
    const poisCount = await db('pois').count('* as count').first();
    const poiShapesCount = await db('poi_shapes').count('* as count').first();
    const highwaysCount = await db('highways').count('* as count').first();
    const highwayShapesCount = await db('highway_shapes').count('* as count').first();

    console.log(`Current counts:
  - POIs: ${poisCount.count}
  - POI shapes: ${poiShapesCount.count}
  - Highways: ${highwaysCount.count}
  - Highway shapes: ${highwayShapesCount.count}
`);

    console.log('\n===== DELETING POIs =====');
    
    // Delete POI shape-POI links
    console.log('Step 1: Deleting poi_shapes_poi_lnk entries...');
    const poiShapeLinkDeleted = await db.raw(`
      DELETE FROM poi_shapes_poi_lnk 
      WHERE poi_id IN (
        SELECT poi_id FROM pois_country_lnk WHERE country_id = ?
      )
    `, [countryId]);
    console.log(`  Deleted ${poiShapeLinkDeleted.rowCount} POI shape-POI links`);

    // Delete orphaned POI shapes
    console.log('Step 2: Deleting orphaned poi_shapes...');
    const poiShapesDeleted = await db.raw(`
      DELETE FROM poi_shapes 
      WHERE id NOT IN (SELECT poi_shape_id FROM poi_shapes_poi_lnk)
    `);
    console.log(`  Deleted ${poiShapesDeleted.rowCount} orphaned POI shapes`);

    // Delete POIs
    console.log('Step 3: Deleting pois...');
    const poisDeleted = await db.raw(`
      DELETE FROM pois 
      WHERE id IN (SELECT poi_id FROM pois_country_lnk WHERE country_id = ?)
    `, [countryId]);
    console.log(`  Deleted ${poisDeleted.rowCount} POIs`);

    // Delete POI-country links
    console.log('Step 4: Deleting pois_country_lnk entries...');
    const poiCountryLinkDeleted = await db('pois_country_lnk')
      .where('country_id', countryId)
      .del();
    console.log(`  Deleted ${poiCountryLinkDeleted} POI-country links`);

    console.log('\n===== DELETING HIGHWAYS =====');
    
    // Delete highway shape-highway links
    console.log('Step 1: Deleting highway_shapes_highway_lnk entries...');
    const highwayShapeLinkDeleted = await db.raw(`
      DELETE FROM highway_shapes_highway_lnk 
      WHERE highway_id IN (
        SELECT highway_id FROM highways_country_lnk WHERE country_id = ?
      )
    `, [countryId]);
    console.log(`  Deleted ${highwayShapeLinkDeleted.rowCount} highway shape-highway links`);

    // Delete orphaned highway shapes
    console.log('Step 2: Deleting orphaned highway_shapes...');
    const highwayShapesDeleted = await db.raw(`
      DELETE FROM highway_shapes 
      WHERE id NOT IN (SELECT highway_shape_id FROM highway_shapes_highway_lnk)
    `);
    console.log(`  Deleted ${highwayShapesDeleted.rowCount} orphaned highway shapes`);

    // Delete highways
    console.log('Step 3: Deleting highways...');
    const highwaysDeleted = await db.raw(`
      DELETE FROM highways 
      WHERE id IN (SELECT highway_id FROM highways_country_lnk WHERE country_id = ?)
    `, [countryId]);
    console.log(`  Deleted ${highwaysDeleted.rowCount} highways`);

    // Delete highway-country links
    console.log('Step 4: Deleting highways_country_lnk entries...');
    const highwayCountryLinkDeleted = await db('highways_country_lnk')
      .where('country_id', countryId)
      .del();
    console.log(`  Deleted ${highwayCountryLinkDeleted} highway-country links`);

    console.log('\n✅ Cleanup complete! Final counts:');
    const finalPois = await db('pois').count('* as count').first();
    const finalPoiShapes = await db('poi_shapes').count('* as count').first();
    const finalHighways = await db('highways').count('* as count').first();
    const finalHighwayShapes = await db('highway_shapes').count('* as count').first();

    console.log(`  - POIs: ${finalPois.count}
  - POI shapes: ${finalPoiShapes.count}
  - Highways: ${finalHighways.count}
  - Highway shapes: ${finalHighwayShapes.count}
`);

  } catch (error) {
    console.error('Error during cleanup:', error);
  } finally {
    await db.destroy();
    process.exit(0);
  }
}

cleanup();
