const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function checkDatabase() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Check permissions table structure
    console.log('\n=== PERMISSIONS TABLE STRUCTURE ===');
    const permissionsSchema = await client.query(`
      SELECT column_name, data_type, is_nullable 
      FROM information_schema.columns 
      WHERE table_name = 'up_permissions' 
      ORDER BY ordinal_position
    `);
    
    console.log('up_permissions columns:');
    permissionsSchema.rows.forEach(col => {
      console.log(`  ${col.column_name} (${col.data_type}) - nullable: ${col.is_nullable}`);
    });

    // Check roles table
    console.log('\n=== ROLES TABLE ===');
    const roles = await client.query('SELECT * FROM up_roles');
    console.log('Available roles:');
    roles.rows.forEach(role => {
      console.log(`  ID: ${role.id}, Name: ${role.name}, Type: ${role.type}`);
    });

    // Check existing permissions
    console.log('\n=== EXISTING PERMISSIONS ===');
    const permissions = await client.query('SELECT * FROM up_permissions LIMIT 5');
    console.log('Sample permissions:');
    permissions.rows.forEach(perm => {
      console.log(`  ${JSON.stringify(perm)}`);
    });

  } catch (error) {
    console.error('❌ Error:', error.message);
  } finally {
    await client.end();
  }
}

checkDatabase();