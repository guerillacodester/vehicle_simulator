// Create users-permissions for agency API
// This allows authenticated users to reach the agency routes where RBAC policy will run

const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!'
});

async function seedPermissions() {
  await client.connect();
  console.log('[Permissions] Connected to database');

  // Get the Authenticated role ID
  const roleResult = await client.query(
    `SELECT id FROM up_roles WHERE type = 'authenticated' LIMIT 1`
  );

  if (roleResult.rows.length === 0) {
    console.error('[Permissions] ❌ Authenticated role not found');
    await client.end();
    return;
  }

  const roleId = roleResult.rows[0].id;
  console.log(`[Permissions] Found authenticated role: ${roleId}`);

  // Agency actions to create permissions for
  const actions = ['find', 'findOne', 'create', 'update', 'delete'];

  for (const action of actions) {
    const actionName = `api::agency.agency.${action}`;

    // Check if permission already exists
    const existing = await client.query(
      `SELECT id, enabled FROM up_permissions WHERE action = $1 AND role = $2`,
      [actionName, roleId]
    );

    if (existing.rows.length > 0) {
      const permId = existing.rows[0].id;
      const wasEnabled = existing.rows[0].enabled;

      // Update to enabled if not already
      if (!wasEnabled) {
        await client.query(
          `UPDATE up_permissions SET enabled = true WHERE id = $1`,
          [permId]
        );
        console.log(`[Permissions] ✅ Enabled: ${actionName}`);
      } else {
        console.log(`[Permissions] ✓ Already enabled: ${actionName}`);
      }
    } else {
      // Create new permission
      await client.query(
        `INSERT INTO up_permissions (action, role, created_at, updated_at)
         VALUES ($1, $2, NOW(), NOW())`,
        [actionName, roleId]
      );
      console.log(`[Permissions] ✅ Created: ${actionName}`);
    }
  }

  await client.end();
  console.log('[Permissions] ✅ Agency permissions seeded successfully');
}

seedPermissions().catch(err => {
  console.error('[Permissions] ❌ Error:', err);
  client.end();
  process.exit(1);
});
