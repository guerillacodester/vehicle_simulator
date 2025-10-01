const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function checkCmsTableStructure() {
  try {
    await client.connect();
    console.log('Connected to database');

    const cmsTables = ['cms_drivers', 'cms_vehicles', 'cms_routes', 'cms_depots'];
    
    for (const table of cmsTables) {
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
        
        // Get all data
        const dataResult = await client.query(`SELECT * FROM ${table}`);
        console.log(`\nData (${dataResult.rows.length} rows):`);
        dataResult.rows.forEach((row, index) => {
          console.log(`  Row ${index + 1}:`, row);
        });
        
      } catch (error) {
        console.log(`  Error accessing table: ${error.message}`);
      }
    }

  } catch (error) {
    console.error('❌ Check failed:', error.message);
  } finally {
    await client.end();
  }
}

checkCmsTableStructure();