const { Client } = require('pg');
const fs = require('fs');

// Remote database connection (via SSH tunnel)
const remoteClient = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function exportDataOnly() {
  try {
    await remoteClient.connect();
    console.log('Connected to remote database');

    const tables = ['cms_vehicles', 'cms_drivers', 'cms_routes', 'cms_depots'];
    let sqlInserts = '-- Data export from remote database\n-- Run this after Strapi creates fresh schema\n\n';

    for (const table of tables) {
      console.log(`\nExporting data from ${table}...`);
      
      // Get data
      const dataResult = await remoteClient.query(`SELECT * FROM ${table}`);
      console.log(`Found ${dataResult.rows.length} rows in ${table}`);

      if (dataResult.rows.length > 0) {
        // Get column names
        const columns = Object.keys(dataResult.rows[0]);
        
        sqlInserts += `-- Data for ${table}\n`;
        
        for (const row of dataResult.rows) {
          const values = columns.map(col => {
            const value = row[col];
            if (value === null) return 'NULL';
            if (typeof value === 'string') {
              return `'${value.replace(/'/g, "''")}'`;
            }
            if (value instanceof Date) {
              return `'${value.toISOString()}'`;
            }
            return value;
          });

          sqlInserts += `INSERT INTO ${table} (${columns.join(', ')}) VALUES (${values.join(', ')}) ON CONFLICT (id) DO NOTHING;\n`;
        }
        sqlInserts += '\n';
      }
    }

    // Write to file
    fs.writeFileSync('data-import.sql', sqlInserts);
    console.log('\n✅ Data exported to data-import.sql');
    console.log('This file contains only INSERT statements to populate the local database');

  } catch (error) {
    console.error('❌ Export failed:', error.message);
  } finally {
    await remoteClient.end();
  }
}

exportDataOnly();