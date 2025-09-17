const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function inspectPermissionsTables() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Check what permission tables exist
    console.log('\n=== PERMISSION TABLES ===');
    const tablesResult = await client.query(`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_name LIKE '%permission%' OR table_name LIKE '%role%'
      ORDER BY table_name
    `);
    
    tablesResult.rows.forEach(table => {
      console.log(`  ${table.table_name}`);
    });

    // Check structure of up_permissions table
    console.log('\n=== UP_PERMISSIONS STRUCTURE ===');
    const permSchemaResult = await client.query(`
      SELECT column_name, data_type, is_nullable, column_default
      FROM information_schema.columns 
      WHERE table_name = 'up_permissions' 
      ORDER BY ordinal_position
    `);
    
    permSchemaResult.rows.forEach(col => {
      console.log(`  ${col.column_name}: ${col.data_type} ${col.is_nullable === 'NO' ? 'NOT NULL' : 'NULL'}`);
    });

    // Check structure of up_roles table
    console.log('\n=== UP_ROLES STRUCTURE ===');
    const rolesSchemaResult = await client.query(`
      SELECT column_name, data_type, is_nullable, column_default
      FROM information_schema.columns 
      WHERE table_name = 'up_roles' 
      ORDER BY ordinal_position
    `);
    
    rolesSchemaResult.rows.forEach(col => {
      console.log(`  ${col.column_name}: ${col.data_type} ${col.is_nullable === 'NO' ? 'NOT NULL' : 'NULL'}`);
    });

    // Sample data from up_roles
    console.log('\n=== SAMPLE ROLES ===');
    const rolesResult = await client.query('SELECT * FROM up_roles LIMIT 5');
    rolesResult.rows.forEach(role => {
      console.log(`  ${role.name} (${role.type}) - ID: ${role.id}`);
    });

    // Sample data from up_permissions
    console.log('\n=== SAMPLE PERMISSIONS ===');
    const permResult = await client.query('SELECT * FROM up_permissions LIMIT 5');
    permResult.rows.forEach(perm => {
      console.log(`  Action: ${perm.action}, Subject: ${perm.subject}, Role ID: ${perm.role_id || perm.role || 'N/A'}`);
    });

  } catch (error) {
    console.error('❌ Inspection failed:', error.message);
  } finally {
    await client.end();
  }
}

inspectPermissionsTables();