const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function inspectTables() {
  try {
    await client.connect();
    console.log('Connected to database');

    const tables = ['drivers', 'vehicles', 'routes', 'depots'];
    
    for (const table of tables) {
      console.log(`\n=== ${table.toUpperCase()} TABLE ===`);
      
      try {
        // Get table structure
        const schemaResult = await client.query(`
          SELECT column_name, data_type, is_nullable, column_default
          FROM information_schema.columns 
          WHERE table_name = $1 
          ORDER BY ordinal_position
        `, [table]);
        
        console.log('Columns:');
        schemaResult.rows.forEach(col => {
          console.log(`  ${col.column_name}: ${col.data_type} ${col.is_nullable === 'NO' ? 'NOT NULL' : 'NULL'} ${col.column_default ? `DEFAULT ${col.column_default}` : ''}`);
        });
        
        // Get sample data
        const dataResult = await client.query(`SELECT * FROM ${table} LIMIT 3`);
        console.log(`\nSample data (${dataResult.rows.length} rows):`);
        dataResult.rows.forEach((row, index) => {
          console.log(`  Row ${index + 1}:`, row);
        });
        
      } catch (error) {
        console.log(`  Error accessing table: ${error.message}`);
      }
    }

    // Also check CMS tables if they exist
    console.log('\n=== CMS TABLES ===');
    const cmsTables = ['cms_drivers', 'cms_vehicles', 'cms_routes', 'cms_depots'];
    
    for (const table of cmsTables) {
      try {
        const result = await client.query(`SELECT COUNT(*) FROM ${table}`);
        console.log(`${table}: ${result.rows[0].count} rows`);
      } catch (error) {
        console.log(`${table}: Does not exist`);
      }
    }

  } catch (error) {
    console.error('❌ Inspection failed:', error.message);
  } finally {
    await client.end();
  }
}

inspectTables();