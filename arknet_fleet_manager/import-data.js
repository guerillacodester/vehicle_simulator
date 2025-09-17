const { Client } = require('pg');
const fs = require('fs');

// Local database connection
const localClient = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'strapi',
  password: 'strapi123',
  ssl: false
});

async function importData() {
  try {
    await localClient.connect();
    console.log('Connected to local database');

    // Read the SQL file
    const sqlContent = fs.readFileSync('data-import.sql', 'utf8');
    
    // Split by lines and filter out comments and empty lines
    const statements = sqlContent
      .split('\n')
      .filter(line => line.trim() && !line.trim().startsWith('--'))
      .join('\n')
      .split(';')
      .filter(stmt => stmt.trim());

    console.log(`Found ${statements.length} SQL statements to execute`);

    for (let i = 0; i < statements.length; i++) {
      const statement = statements[i].trim();
      if (statement) {
        try {
          await localClient.query(statement);
          console.log(`✅ Statement ${i + 1}/${statements.length} executed`);
        } catch (error) {
          console.log(`⚠️  Statement ${i + 1} failed: ${error.message}`);
          // Continue with other statements
        }
      }
    }

    console.log('\n🎉 Data import completed!');

    // Verify the import
    const tables = ['cms_vehicles', 'cms_drivers', 'cms_routes', 'cms_depots'];
    console.log('\n=== Import Verification ===');
    
    for (const table of tables) {
      try {
        const result = await localClient.query(`SELECT COUNT(*) FROM ${table}`);
        console.log(`${table}: ${result.rows[0].count} rows`);
      } catch (error) {
        console.log(`${table}: Table not found or error - ${error.message}`);
      }
    }

  } catch (error) {
    console.error('❌ Import failed:', error.message);
  } finally {
    await localClient.end();
  }
}

importData();