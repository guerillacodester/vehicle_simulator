const { Client } = require('pg');
const fs = require('fs');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function exportData() {
  try {
    await client.connect();
    console.log('Connected to database');

    const tables = ['cms_vehicles', 'cms_drivers', 'cms_routes', 'cms_depots'];
    let sqlContent = '-- Exported data from arknettransit database\n\n';

    for (const table of tables) {
      console.log(`\nExporting ${table}...`);
      
      // Get table structure
      const schemaResult = await client.query(`
        SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = $1 
        ORDER BY ordinal_position
      `, [table]);

      // Create table SQL
      sqlContent += `-- Table: ${table}\n`;
      sqlContent += `DROP TABLE IF EXISTS ${table} CASCADE;\n`;
      sqlContent += `CREATE TABLE ${table} (\n`;
      
      const columns = schemaResult.rows.map(col => {
        let colDef = `  ${col.column_name} `;
        
        // Map PostgreSQL types
        switch (col.data_type) {
          case 'character varying':
            colDef += col.character_maximum_length ? `VARCHAR(${col.character_maximum_length})` : 'VARCHAR';
            break;
          case 'integer':
            colDef += 'INTEGER';
            break;
          case 'timestamp without time zone':
            colDef += 'TIMESTAMP';
            break;
          case 'geometry':
            colDef += 'TEXT'; // Simplify geometry for now
            break;
          default:
            colDef += col.data_type.toUpperCase();
        }

        if (col.is_nullable === 'NO') {
          colDef += ' NOT NULL';
        }

        if (col.column_default) {
          if (col.column_default.includes('nextval')) {
            colDef = colDef.replace('INTEGER', 'SERIAL');
          } else {
            colDef += ` DEFAULT ${col.column_default}`;
          }
        }

        return colDef;
      });

      sqlContent += columns.join(',\n') + '\n);\n\n';

      // Get data
      const dataResult = await client.query(`SELECT * FROM ${table}`);
      console.log(`Found ${dataResult.rows.length} rows in ${table}`);

      if (dataResult.rows.length > 0) {
        const columnNames = schemaResult.rows.map(col => col.column_name);
        
        sqlContent += `-- Data for ${table}\n`;
        
        for (const row of dataResult.rows) {
          const values = columnNames.map(col => {
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

          sqlContent += `INSERT INTO ${table} (${columnNames.join(', ')}) VALUES (${values.join(', ')});\n`;
        }
        sqlContent += '\n';
      }
    }

    // Write to file
    fs.writeFileSync('database-export.sql', sqlContent);
    console.log('\n✅ Database exported to database-export.sql');
    console.log('This file can be used to recreate the database locally');

  } catch (error) {
    console.error('❌ Export failed:', error.message);
  } finally {
    await client.end();
  }
}

exportData();