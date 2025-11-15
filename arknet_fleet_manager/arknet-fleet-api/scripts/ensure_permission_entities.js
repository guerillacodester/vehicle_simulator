#!/usr/bin/env node
/**
 * Ensure that custom Users & Permissions actions exist in the up_permissions table.
 *
 * This script inserts rows for any missing custom actions so that the
 * sync_permissions.js script can link them to the appropriate roles.
 */

require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const { Client } = require('pg');

const REQUIRED_ACTIONS = [
  { action: 'api::route.route.getGeometry', note: 'Route geometry query' },
  { action: 'api::country.import-geojson.importFromFile', note: 'Country GeoJSON import (file)' },
  { action: 'api::country.import-geojson.importDirect', note: 'Country GeoJSON import (direct)' },
  { action: 'api::user-profile.user-profile.create', note: 'User profile create' },
  { action: 'api::user-profile.user-profile.update', note: 'User profile update' },
  { action: 'api::user-profile.user-profile.delete', note: 'User profile delete' },
];

async function main() {
  const client = new Client({
    host: process.env.DATABASE_HOST || 'localhost',
    port: Number(process.env.DATABASE_PORT || 5432),
    database: process.env.DATABASE_NAME,
    user: process.env.DATABASE_USERNAME,
    password: process.env.DATABASE_PASSWORD,
  });

  await client.connect();

  const actions = REQUIRED_ACTIONS.map((item) => item.action);
  const existing = await client.query('SELECT action FROM up_permissions WHERE action = ANY($1)', [actions]);
  const existingSet = new Set(existing.rows.map((row) => row.action));
  const existingCount = existingSet.size;

  let created = 0;
  for (const item of REQUIRED_ACTIONS) {
    if (existingSet.has(item.action)) {
      console.log(`✔ permission already exists: ${item.action}`);
      continue;
    }

    const res = await client.query(
      'INSERT INTO up_permissions(action, created_at, updated_at) VALUES($1, NOW(), NOW()) RETURNING id',
      [item.action]
    );
    created += 1;
    console.log(`➕ created permission row ${res.rows[0].id} for ${item.action} (${item.note})`);
  }

  console.log(`ensure_permission_entities: created=${created}, existing=${existingCount}`);
  await client.end();
}

main().catch((err) => {
  console.error('ensure_permission_entities failed:', err);
  process.exit(1);
});
