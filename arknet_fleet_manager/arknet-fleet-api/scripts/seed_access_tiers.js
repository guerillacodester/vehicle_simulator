// Seed script for AccessTier table in Strapi
// Run with: node scripts/seed_access_tiers.js

const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!'
});

const tiers = [
  'SuperAdmin',
  'Admin',
  'Manager',
  'Dispatcher',
  'Operator',
  'Viewer',
  'Guest'
];

async function seed() {
  await client.connect();
  for (const tier of tiers) {
    await client.query(
      `INSERT INTO access_tiers (name) VALUES ($1) ON CONFLICT (name) DO NOTHING`,
      [tier]
    );
    console.log(`Seeded: ${tier}`);
  }
  await client.end();
  console.log('AccessTier seeding complete.');
}

seed().catch(err => {
  console.error('Seeding error:', err);
  client.end();
});
