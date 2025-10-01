const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'strapi',
  password: 'strapi123',
  ssl: false
});

async function checkPublicationState() {
  try {
    await client.connect();
    console.log('Connected to database');

    const tables = ['cms_vehicles', 'cms_drivers', 'cms_routes', 'cms_depots'];
    
    for (const table of tables) {
      console.log(`\n=== ${table} ===`);
      const result = await client.query(`
        SELECT id, document_id, published_at, created_at, updated_at 
        FROM ${table} 
        ORDER BY id
      `);
      
      console.log(`Found ${result.rows.length} records:`);
      result.rows.forEach(row => {
        const publishedStatus = row.published_at ? '✅ Published' : '❌ Draft';
        console.log(`  ID: ${row.id}, DocumentID: ${row.document_id}, ${publishedStatus}`);
      });

      // Check if any records are not published
      const unpublishedCount = result.rows.filter(row => !row.published_at).length;
      if (unpublishedCount > 0) {
        console.log(`\n⚠️  ${unpublishedCount} records are not published. Publishing them...`);
        await client.query(`
          UPDATE ${table} 
          SET published_at = NOW(), updated_at = NOW() 
          WHERE published_at IS NULL
        `);
        console.log(`✅ Published all records in ${table}`);
      }
    }

    console.log('\n🎉 Publication state check complete!');

  } catch (error) {
    console.error('❌ Check failed:', error.message);
  } finally {
    await client.end();
  }
}

checkPublicationState();