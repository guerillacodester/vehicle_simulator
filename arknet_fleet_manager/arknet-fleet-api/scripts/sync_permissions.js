#!/usr/bin/env node
// Sync permissions to DB based on route minTier metadata.
// - loads environment from ../.env
// - scans src/api routes for handlers and minTier
// - applies mapping to up_permissions + up_permissions_role_lnk if present
//
// Run from arknet-fleet-api with: node scripts/sync_permissions.js

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

const API_SRC = path.join(__dirname, '../src/api');

function walk(dir, filelist = []) {
  const files = fs.readdirSync(dir);
  files.forEach((file) => {
    const filepath = path.join(dir, file);
    const stat = fs.statSync(filepath);
    if (stat.isDirectory()) walk(filepath, filelist);
    else filelist.push(filepath);
  });
  return filelist;
}

function findRouteFiles() {
  const files = [];
  if (!fs.existsSync(API_SRC)) return files;
  const all = walk(API_SRC);
  for (const f of all) {
    if (/\\routes\\.*\.(js|ts)$/.test(f)) files.push(f);
  }
  return files;
}

function extractHandlersAndTiers(fileContent) {
  const results = [];

  // Find handler entries like handler: 'controller.action' or handler: "controller.action"
  const handlerRe = /handler\s*:\s*['\"]([\w\-\.]+)['\"]/g;
  let m;
  const handlers = [];
  while ((m = handlerRe.exec(fileContent)) !== null) {
    handlers.push({ handler: m[1], index: m.index });
  }

  // Also try to find simple controller.action strings (controller.action)
  if (handlers.length === 0) {
    const simpleRe = /([\w\-]+\.[a-zA-Z0-9_]+)\s*(?:,|\n|\r|})/g;
    while ((m = simpleRe.exec(fileContent)) !== null) {
      // skip if looks like import path
      if (m[1].includes('/')) continue;
      handlers.push({ handler: m[1], index: m.index });
    }
  }

  // Find all minTier occurrences
  const minTierRe = /minTier\s*:\s*['\"]([^'\"]+)['\"]/ig;
  const tiers = [];
  while ((m = minTierRe.exec(fileContent)) !== null) {
    tiers.push({ tier: m[1], index: m.index });
  }

  // For each handler, try to find nearest minTier after it (within 500 chars window)
  for (const h of handlers) {
    let nearest = undefined;
    let bestDist = Infinity;
    for (const t of tiers) {
      const dist = t.index - h.index;
      if (dist >= 0 && dist < 500 && dist < bestDist) {
        bestDist = dist;
        nearest = t.tier;
      }
    }
    results.push({ handler: h.handler, minTier: nearest });
  }

  return results;
}

function normalizeTier(t) {
  if (!t) return undefined;
  const s = String(t).trim().toLowerCase();
  if (s.includes('guest')) return 'Guest';
  if (s.includes('viewer')) return 'Viewer';
  if (s.includes('operator')) return 'Operator';
  if (s.includes('admin')) return 'Admin';
  return t;
}

function decideDesired(minTier, actionName) {
  // returns { auth: bool, pub: bool }
  const tier = normalizeTier(minTier);
  const action = String(actionName || '').split('.').pop();
  if (tier === 'Guest') return { auth: true, pub: true };
  if (tier === 'Viewer') return { auth: true, pub: false };
  if (tier === 'Operator' || tier === 'Admin') return { auth: false, pub: false };
  // default: if no tier and action is read-like, enable for authenticated
  if (!tier && (action === 'find' || action === 'findOne')) return { auth: true, pub: false };
  return { auth: false, pub: false };
}

(async () => {
  const routeFiles = findRouteFiles();
  if (routeFiles.length === 0) {
    console.error('[sync_permissions] No route files found under src/api. Aborting.');
    process.exit(1);
  }

  // Build desired map: actionString -> {auth, pub}
  const desired = {}; // action -> {auth, pub}

  for (const rf of routeFiles) {
    const rel = path.relative(path.join(__dirname, '..'), rf);
    const apiMatch = rf.match(/src\\api\\([^\\]+)\\routes/);
    const apiName = apiMatch ? apiMatch[1] : null;
    const txt = fs.readFileSync(rf, 'utf8');
    const entries = extractHandlersAndTiers(txt);
    for (const e of entries) {
      const handler = e.handler; // e.g., 'route.find' or 'route.findOne'
      if (!apiName) continue;
      const action = `api::${apiName}.${handler}`; // matches DB pattern seen earlier
      const d = decideDesired(e.minTier, handler);
      // Merge with existing: if any entry wants public=true, keep it
      if (!desired[action]) desired[action] = { auth: false, pub: false, sources: [] };
      desired[action].auth = desired[action].auth || d.auth;
      desired[action].pub = desired[action].pub || d.pub;
      desired[action].sources.push({ file: rel, handler, minTier: e.minTier });
    }
  }

  // Special-case: ensure admin-level public find is enabled (previous behavior)
  desired['api::admin-level.admin-level.find'] = desired['api::admin-level.admin-level.find'] || { auth: true, pub: true, sources: [{ note: 'special-case' }] };

  // Connect to DB
  const client = new Client({
    host: process.env.DATABASE_HOST || 'localhost',
    port: Number(process.env.DATABASE_PORT || 5432),
    database: process.env.DATABASE_NAME || 'arknettransit',
    user: process.env.DATABASE_USERNAME || 'postgres',
    password: process.env.DATABASE_PASSWORD || '',
  });

  try {
    await client.connect();

    // find role table
    const roleCandidates = [
      'plugin_users_permissions_role',
      'up_roles',
      'roles',
    ];
    let roleRows = { rows: [] };
    let roleTbl = null;
    for (const rtbl of roleCandidates) {
      try {
        roleRows = await client.query(`SELECT id, type FROM ${rtbl} WHERE type IN ('public','authenticated')`);
        if (roleRows.rows.length > 0) {
          roleTbl = rtbl; break;
        }
      } catch (e) { }
    }
    if (!roleTbl) {
      console.error('[sync_permissions] Could not find roles table (plugin_users_permissions_role / up_roles / roles). Aborting.');
      process.exit(1);
    }
    const roleByType = {};
    for (const r of roleRows.rows) roleByType[r.type] = r.id;
    console.log('[sync_permissions] role table:', roleTbl, 'found roles:', roleByType);

    // prefer up_permissions path
    let usesUpPermissions = false;
    try {
      await client.query('SELECT 1 FROM up_permissions LIMIT 1');
      usesUpPermissions = true;
    } catch (e) { usesUpPermissions = false; }

    let inserted = 0, deleted = 0, skipped = 0, updated = 0;

    for (const [action, info] of Object.entries(desired)) {
      if (usesUpPermissions) {
        // find permission id
        const p = await client.query('SELECT id FROM up_permissions WHERE action = $1', [action]);
        if (p.rows.length === 0) {
          console.log(`[sync_permissions] permission not found in up_permissions, skipping: ${action}`);
          skipped++;
          continue;
        }
        const pid = p.rows[0].id;
        // get existing role links
        const links = await client.query('SELECT role_id FROM up_permissions_role_lnk WHERE permission_id = $1', [pid]);
        const existingRoleIds = new Set(links.rows.map(r => String(r.role_id)));

        // authenticated
        const authId = roleByType['authenticated'];
        if (authId) {
          const should = !!info.auth;
          const exists = existingRoleIds.has(String(authId));
          if (should && !exists) {
            await client.query('INSERT INTO up_permissions_role_lnk(permission_id, role_id) VALUES($1,$2)', [pid, authId]);
            inserted++;
            console.log(`[sync_permissions] linked auth ${authId} -> ${action}`);
          } else if (!should && exists) {
            await client.query('DELETE FROM up_permissions_role_lnk WHERE permission_id = $1 AND role_id = $2', [pid, authId]);
            deleted++;
            console.log(`[sync_permissions] unlinked auth ${authId} -/-> ${action}`);
          }
        }

        // public
        const pubId = roleByType['public'];
        if (pubId) {
          const should = !!info.pub;
          const exists = existingRoleIds.has(String(pubId));
          if (should && !exists) {
            await client.query('INSERT INTO up_permissions_role_lnk(permission_id, role_id) VALUES($1,$2)', [pid, pubId]);
            inserted++;
            console.log(`[sync_permissions] linked public ${pubId} -> ${action}`);
          } else if (!should && exists) {
            await client.query('DELETE FROM up_permissions_role_lnk WHERE permission_id = $1 AND role_id = $2', [pid, pubId]);
            deleted++;
            console.log(`[sync_permissions] unlinked public ${pubId} -/-> ${action}`);
          }
        }

      } else {
        // fallback: plugin_users_permissions_permission table where rows include role column
        const permCandidates = ['plugin_users_permissions_permission', 'permissions'];
        let usedTbl = null;
        for (const ptbl of permCandidates) {
          try {
            const test = await client.query(`SELECT id FROM ${ptbl} LIMIT 1`);
            usedTbl = ptbl; break;
          } catch (e) { }
        }
        if (!usedTbl) {
          console.warn('[sync_permissions] No permission table found to update for action', action);
          skipped++; continue;
        }

        // update/insert for auth
        for (const [tname, shouldFlag] of [['authenticated', info.auth], ['public', info.pub]]) {
          const roleId = roleByType[tname];
          if (!roleId) continue;
          // try update
          const res = await client.query(`UPDATE ${usedTbl} SET enabled = $1 WHERE role = $2 AND action = $3 RETURNING id`, [shouldFlag, roleId, action]);
          if (res.rowCount === 0 && shouldFlag) {
            try {
              await client.query(`INSERT INTO ${usedTbl}(action, role, enabled) VALUES($1,$2,$3)`, [action, roleId, shouldFlag]);
              inserted++; console.log(`[sync_permissions] inserted ${usedTbl} row for role ${tname} action ${action}`);
            } catch (e) { console.warn('[sync_permissions] insert failed', e.message); skipped++; }
          } else if (res.rowCount > 0) {
            updated++;
            console.log(`[sync_permissions] updated ${usedTbl} for role ${tname} action ${action} -> ${shouldFlag}`);
          }
        }
      }
    }

    console.log('\n[sync_permissions] done. inserted=%d deleted=%d updated=%d skipped=%d', inserted, deleted, updated, skipped);

    // Print a short summary: for each role, count API permissions
    try {
      if (usesUpPermissions) {
        for (const t of ['public','authenticated']) {
          const rid = roleByType[t];
          if (!rid) continue;
          const r = await client.query(`SELECT COUNT(*) FROM up_permissions_role_lnk lnk JOIN up_permissions p ON p.id = lnk.permission_id WHERE lnk.role_id = $1 AND p.action LIKE 'api::%'`, [rid]);
          console.log(`[sync_permissions] role ${t} (id=${rid}) now has ${r.rows[0].count} api::* permissions`);
        }
      }
    } catch (e) { /* ignore */ }

    await client.end();
    process.exit(0);
  } catch (err) {
    console.error('[sync_permissions] Error:', err);
    try { await client.end(); } catch (e) {}
    process.exit(1);
  }
})();
