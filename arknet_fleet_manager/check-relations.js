const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function checkRelations() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Find all tables related to permissions and roles
    console.log('\n=== TABLES WITH "permission" OR "role" IN NAME ===');
    const tables = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND (table_name LIKE '%permission%' OR table_name LIKE '%role%')
      ORDER BY table_name
    `);
    
    console.log('Related tables:');
    tables.rows.forEach(table => {
      console.log(`  ${table.table_name}`);
    });

    // Check for link tables
    console.log('\n=== LINK TABLES ===');
    const linkTables = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public' 
      AND table_name LIKE '%links%'
      ORDER BY table_name
    `);
    
    console.log('Link tables:');
    linkTables.rows.forEach(table => {
      console.log(`  ${table.table_name}`);
    });

    // If there are link tables, check their structure
    if (linkTables.rows.length > 0) {
      for (const table of linkTables.rows) {
        if (table.table_name.includes('permission') || table.table_name.includes('role')) {
          console.log(`\n=== ${table.table_name.toUpperCase()} STRUCTURE ===`);
          const schema = await client.query(`
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = $1
            ORDER BY ordinal_position
          `, [table.table_name]);
          
          schema.rows.forEach(col => {
            console.log(`  ${col.column_name} (${col.data_type}) - nullable: ${col.is_nullable}`);
          });

          // Show sample data
          const sample = await client.query(`SELECT * FROM ${table.table_name} LIMIT 3`);
          console.log('Sample data:');
          sample.rows.forEach(row => {
            console.log(`  ${JSON.stringify(row)}`);
          });
        }
      }
    }

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

checkRelations();