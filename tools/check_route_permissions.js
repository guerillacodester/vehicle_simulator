const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!'
});

async function checkPermissions() {
  try {
    await client.connect();
    
    // Check ALL route actions for authenticated role
    const result = await client.query(`
      SELECT p.id, p.action, p.published_at, r.type as role_type
      FROM up_permissions p
      JOIN up_permissions_role_lnk l ON p.id = l.permission_id
      JOIN up_roles r ON l.role_id = r.id
      WHERE p.action LIKE 'api::route.route.%'
        AND r.type = 'authenticated'
      ORDER BY p.action
    `);
    
    console.log('Route permissions in users-permissions:');
    console.log(JSON.stringify(result.rows, null, 2));
    
  } catch (error) {
    console.error('Error:', error.message);
  } finally {
    await client.end();
  }
}

checkPermissions();
