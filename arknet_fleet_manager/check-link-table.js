const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function checkLinkTable() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Check the permission-role link table structure
    console.log('\n=== up_permissions_role_lnk STRUCTURE ===');
    const schema = await client.query(`
      SELECT column_name, data_type, is_nullable 
      FROM information_schema.columns 
      WHERE table_name = 'up_permissions_role_lnk'
      ORDER BY ordinal_position
    `);
    
    schema.rows.forEach(col => {
      console.log(`  ${col.column_name} (${col.data_type}) - nullable: ${col.is_nullable}`);
    });

    // Show sample data
    console.log('\n=== SAMPLE LINK DATA ===');
    const sample = await client.query('SELECT * FROM up_permissions_role_lnk LIMIT 5');
    sample.rows.forEach(row => {
      console.log(`  ${JSON.stringify(row)}`);
    });

    // Check what permissions are already linked to the public role (ID: 2)
    console.log('\n=== CURRENT PUBLIC ROLE PERMISSIONS ===');
    const publicPerms = await client.query(`
      SELECT p.action, p.document_id, l.permission_id, l.role_id
      FROM up_permissions p
      JOIN up_permissions_role_lnk l ON p.id = l.permission_id
      WHERE l.role_id = 2
    `);
    
    console.log(`Found ${publicPerms.rows.length} permissions for public role:`);
    publicPerms.rows.forEach(perm => {
      console.log(`  ${perm.action}`);
    });

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

checkLinkTable();