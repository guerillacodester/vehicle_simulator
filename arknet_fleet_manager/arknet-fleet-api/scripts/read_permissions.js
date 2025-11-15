#!/usr/bin/env node
/**
 * Read plugin::users-permissions.permission entries using direct DB query
 * - loads environment variables from .env using dotenv
 * - uses pg (node-postgres) to connect to DB
 * - queries permissions for public and authenticated roles
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const { Client } = require('pg');

(async () => {
  const client = new Client({
    host: process.env.DATABASE_HOST || 'localhost',
    port: Number(process.env.DATABASE_PORT || 5432),
    database: process.env.DATABASE_NAME || 'arknettransit',
    user: process.env.DATABASE_USERNAME || 'postgres',
    password: process.env.DATABASE_PASSWORD || '',
  });

  try {
    await client.connect();

    // Resolve role ids
    // Some Strapi installations use prefixed table names (e.g., up_roles/up_permissions). We will try to find the roles table
    const roleCandidates = [
      "plugin_users_permissions_role",
      "up_roles",
      "roles",
    ];

    let roleRows = { rows: [] };
    for (const rtbl of roleCandidates) {
      try {
        roleRows = await client.query(`SELECT id, type FROM ${rtbl} WHERE type IN ('public','authenticated')`);
        if (roleRows.rows.length > 0) {
          console.log(`[read_permissions] Using role table: ${rtbl}`);
          break;
        }
      } catch (e) {
        // ignore and try next
      }
    }
    const roleByType = {};
    for (const r of roleRows.rows) roleByType[r.type] = r.id;

    const actionsLike = 'api::%';

    for (const type of ['public', 'authenticated']) {
      const roleId = roleByType[type];
      console.log(`\nPermissions for role: ${type} (id=${roleId})`);
      if (!roleId) {
        console.log('  > Role not found in DB');
        continue;
      }

      // Try different permission table names
      const permCandidates = ['plugin_users_permissions_permission', 'up_permissions', 'permissions'];
      let res = { rows: [] };
      // For up_permissions we need to join the role link table up_permissions_role_lnk
      if (roleId && permCandidates.includes('up_permissions')) {
        try {
          res = await client.query(
            `SELECT p.id, p.action FROM up_permissions p JOIN up_permissions_role_lnk lnk ON lnk.permission_id = p.id WHERE lnk.role_id = $1 AND p.action LIKE $2 ORDER BY p.action`,
            [roleId, actionsLike]
          );
        } catch (e) {
          // ignore
        }
      }
      for (const ptbl of permCandidates) {
        try {
          res = await client.query(`SELECT id, action, enabled FROM ${ptbl} WHERE role = $1 AND action LIKE $2 ORDER BY action`, [roleId, actionsLike]);
          if (res.rows.length > 0) {
            console.log(`[read_permissions] Using permission table: ${ptbl}`);
            break;
          }
        } catch (e) {
          // ignore and continue
        }
      }

      if (res.rows.length === 0) {
        console.log('  > No permissions found');
      } else {
        console.table(res.rows);
      }
    }

    // Optional: list all api::* actions
    // All perms - search for either name
    const permCandidates = ['plugin_users_permissions_permission', 'up_permissions', 'permissions'];
    let all = { rows: [] };
    for (const ptbl of permCandidates) {
      try {
        if (ptbl === 'up_permissions') {
          all = await client.query(`SELECT p.id AS id, lnk.role_id AS role, p.action AS action, true AS enabled FROM up_permissions p JOIN up_permissions_role_lnk lnk ON lnk.permission_id = p.id WHERE p.action LIKE $1 ORDER BY p.action`, [actionsLike]);
        } else {
          all = await client.query(`SELECT id, role, action, enabled FROM ${ptbl} WHERE action LIKE $1 ORDER BY action`, [actionsLike]);
        }
        if (all.rows.length > 0) break;
      } catch (e) { /* ignore */ }
    }
    console.log('\nSummary of API permissions (all roles):');
    console.table(all.rows);

    await client.end();
  } catch (err) {
    console.error('Error connecting to DB:', err);
    process.exit(1);
  }
})();
