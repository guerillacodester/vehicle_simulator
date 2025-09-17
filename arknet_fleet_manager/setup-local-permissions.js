const { Client } = require('pg');
const { v4: uuidv4 } = require('uuid');

// Local database connection
const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'strapi',
  password: 'strapi123',
  ssl: false
});

async function setupPermissions() {
  try {
    await client.connect();
    console.log('Connected to local database');

    const publicRoleId = 2; // Standard public role ID
    const contentTypes = ['vehicle', 'driver', 'route', 'depot'];
    const actions = ['find', 'findOne'];

    console.log(`Setting up permissions for Public role (ID: ${publicRoleId})`);

    for (const contentType of contentTypes) {
      for (const action of actions) {
        const actionName = `api::${contentType}.${contentType}.${action}`;
        
        // Check if permission already exists
        const existingPermission = await client.query(
          'SELECT * FROM up_permissions WHERE action = $1',
          [actionName]
        );

        let permissionId;

        if (existingPermission.rows.length === 0) {
          // Create new permission
          const documentId = uuidv4().replace(/-/g, '').substring(0, 24); // Generate 24-char ID
          const result = await client.query(
            `INSERT INTO up_permissions (document_id, action, created_at, updated_at, published_at) 
             VALUES ($1, $2, NOW(), NOW(), NOW()) RETURNING id`,
            [documentId, actionName]
          );
          permissionId = result.rows[0].id;
          console.log(`✅ Created permission: ${actionName} (ID: ${permissionId})`);
        } else {
          permissionId = existingPermission.rows[0].id;
          console.log(`• Permission already exists: ${actionName} (ID: ${permissionId})`);
        }

        // Check if the permission is already linked to the public role
        const existingLink = await client.query(
          'SELECT * FROM up_permissions_role_lnk WHERE permission_id = $1 AND role_id = $2',
          [permissionId, publicRoleId]
        );

        if (existingLink.rows.length === 0) {
          // Create the link between permission and role
          await client.query(
            `INSERT INTO up_permissions_role_lnk (permission_id, role_id, permission_ord) 
             VALUES ($1, $2, 1)`,
            [permissionId, publicRoleId]
          );
          console.log(`✅ Linked permission to public role: ${actionName}`);
        } else {
          console.log(`• Permission already linked to public role: ${actionName}`);
        }
      }
    }

    console.log('\n🎉 Permissions setup complete!');
    console.log('APIs should now be accessible to public users!');

  } catch (error) {
    console.error('❌ Setup failed:', error.message);
    console.error(error.stack);
  } finally {
    await client.end();
  }
}

setupPermissions();