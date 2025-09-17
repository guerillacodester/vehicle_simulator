const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function setupPermissions() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Find the Public role (this is what anonymous users use)
    const rolesResult = await client.query('SELECT * FROM up_roles WHERE type = $1', ['public']);
    if (rolesResult.rows.length === 0) {
      console.log('❌ No public role found!');
      return;
    }

    const publicRole = rolesResult.rows[0];
    console.log(`Setting up permissions for Public role (ID: ${publicRole.id})`);

    // Content types to grant permissions for
    const contentTypes = ['vehicle', 'driver', 'route', 'depot'];
    const actions = ['find', 'findOne'];

    for (const contentType of contentTypes) {
      for (const action of actions) {
        const actionName = `api::${contentType}.${contentType}.${action}`;
        
        // Check if permission already exists
        const existingPermission = await client.query(
          'SELECT * FROM up_permissions WHERE role = $1 AND action = $2',
          [publicRole.id, actionName]
        );

        if (existingPermission.rows.length === 0) {
          // Create new permission
          await client.query(
            'INSERT INTO up_permissions (role, action, enabled, created_at, updated_at) VALUES ($1, $2, $3, NOW(), NOW())',
            [publicRole.id, actionName, true]
          );
          console.log(`✅ Created ${action} permission for ${contentType}`);
        } else {
          // Update existing permission to be enabled
          await client.query(
            'UPDATE up_permissions SET enabled = $1, updated_at = NOW() WHERE id = $2',
            [true, existingPermission.rows[0].id]
          );
          console.log(`✅ Updated ${action} permission for ${contentType}`);
        }
      }
    }

    console.log('🎉 Permissions setup complete!');
    console.log('APIs should now be accessible!');

  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.error(error.stack);
  } finally {
    await client.end();
  }
}

setupPermissions();