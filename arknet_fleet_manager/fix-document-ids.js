const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function fixDocumentIds() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Fix document_ids for all CMS tables
    const tables = ['cms_drivers', 'cms_vehicles', 'cms_routes', 'cms_depots'];
    
    for (const table of tables) {
      console.log(`\n=== Fixing ${table.toUpperCase()} ===`);
      
      // Update all rows to have UUIDs for document_id
      const result = await client.query(`
        UPDATE ${table} 
        SET document_id = gen_random_uuid()::varchar 
        WHERE document_id IS NULL
      `);
      
      console.log(`✓ Updated ${result.rowCount} rows with document_ids`);
      
      // Verify the update
      const checkResult = await client.query(`SELECT id, document_id, 
        CASE 
          WHEN '${table}' = 'cms_drivers' THEN name
          WHEN '${table}' = 'cms_vehicles' THEN registration
          WHEN '${table}' = 'cms_routes' THEN code
          WHEN '${table}' = 'cms_depots' THEN name
        END as identifier
        FROM ${table} ORDER BY id`);
      
      checkResult.rows.forEach(row => {
        console.log(`  ID ${row.id}: ${row.identifier} -> document_id: ${row.document_id}`);
      });
    }

    console.log('\n✅ All document_ids fixed!');

  } catch (error) {
    console.error('❌ Fix failed:', error.message);
    console.error(error.stack);
  } finally {
    await client.end();
  }
}

fixDocumentIds();