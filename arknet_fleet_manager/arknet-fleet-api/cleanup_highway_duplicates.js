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
    console.log('Counting current records...');
    const shapesCount = await db('highway_shapes').count('* as count').first();
    const highwaysCount = await db('highways').count('* as count').first();
    const shapeLinkCount = await db('highway_shapes_highway_lnk').count('* as count').first();
    const countryLinkCount = await db('highways_country_lnk').count('* as count').first();

    console.log(`Current counts:
  - Highway shapes: ${shapesCount.count}
  - Highways: ${highwaysCount.count}
  - Shape-highway links: ${shapeLinkCount.count}
  - Highway-country links: ${countryLinkCount.count}
`);

    const countryId = 29; // Barbados
    
    console.log('\nDeleting all highway-related data for Barbados (country_id=29)...');
    
    // Delete shape-highway links
    console.log('Step 1: Deleting highway_shapes_highway_lnk entries...');
    const shapeLinkDeleted = await db.raw(`
      DELETE FROM highway_shapes_highway_lnk 
      WHERE highway_id IN (
        SELECT highway_id FROM highways_country_lnk WHERE country_id = ?
      )
    `, [countryId]);
    console.log(`  Deleted ${shapeLinkDeleted.rowCount} shape-highway links`);

    // Delete orphaned shapes
    console.log('Step 2: Deleting orphaned highway_shapes...');
    const shapesDeleted = await db.raw(`
      DELETE FROM highway_shapes 
      WHERE id NOT IN (SELECT highway_shape_id FROM highway_shapes_highway_lnk)
    `);
    console.log(`  Deleted ${shapesDeleted.rowCount} orphaned shapes`);

    // Delete highways
    console.log('Step 3: Deleting highways...');
    const highwaysDeleted = await db.raw(`
      DELETE FROM highways 
      WHERE id IN (SELECT highway_id FROM highways_country_lnk WHERE country_id = ?)
    `, [countryId]);
    console.log(`  Deleted ${highwaysDeleted.rowCount} highways`);

    // Delete country links
    console.log('Step 4: Deleting highways_country_lnk entries...');
    const countryLinkDeleted = await db('highways_country_lnk')
      .where('country_id', countryId)
      .del();
    console.log(`  Deleted ${countryLinkDeleted} country links`);

    console.log('\n✅ Cleanup complete! Final counts:');
    const finalShapes = await db('highway_shapes').count('* as count').first();
    const finalHighways = await db('highways').count('* as count').first();
    const finalShapeLink = await db('highway_shapes_highway_lnk').count('* as count').first();
    const finalCountryLink = await db('highways_country_lnk').count('* as count').first();

    console.log(`  - Highway shapes: ${finalShapes.count}
  - Highways: ${finalHighways.count}
  - Shape-highway links: ${finalShapeLink.count}
  - Highway-country links: ${finalCountryLink.count}
`);

  } catch (error) {
    console.error('Error during cleanup:', error);
  } finally {
    await db.destroy();
    process.exit(0);
  }
}

cleanup();
