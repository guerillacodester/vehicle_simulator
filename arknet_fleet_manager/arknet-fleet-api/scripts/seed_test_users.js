// Seed script for test users with access tiers in Strapi
// Run with: node scripts/seed_test_users.js

const { Client } = require('pg');
const bcrypt = require('bcryptjs');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!'
});

const users = [
  { username: 'guest', email: 'guest@example.com', password: 'guestpass', tier: 'Guest' },
  { username: 'dispatcher', email: 'dispatcher@example.com', password: 'dispatcherpass', tier: 'Dispatcher' },
  { username: 'admin', email: 'admin@example.com', password: 'adminpass', tier: 'Admin' }
];

async function seed() {
  await client.connect();

  for (const user of users) {
    // Hash the password
    const hashedPassword = await bcrypt.hash(user.password, 10);

    // Insert user
    const userRes = await client.query(
      `INSERT INTO up_users (username, email, password, provider, confirmed, blocked, created_at, updated_at)
       VALUES ($1, $2, $3, 'local', true, false, NOW(), NOW())
       ON CONFLICT (username) DO NOTHING RETURNING id`,
      [user.username, user.email, hashedPassword]
    );

    if (userRes.rows.length > 0) {
      const userId = userRes.rows[0].id;

      // Insert user profile
      const profileRes = await client.query(
        `INSERT INTO user_profiles (user_id, created_at, updated_at)
         VALUES ($1, NOW(), NOW())
         ON CONFLICT (user_id) DO NOTHING RETURNING id`,
        [userId]
      );

      if (profileRes.rows.length > 0) {
        const profileId = profileRes.rows[0].id;

        // Get tier id
        const tierRes = await client.query(
          `SELECT id FROM access_tiers WHERE name = $1`,
          [user.tier]
        );

        if (tierRes.rows.length > 0) {
          const tierId = tierRes.rows[0].id;

          // Link profile to tier
          await client.query(
            `INSERT INTO user_profiles_access_tier_lnk (user_profile_id, access_tier_id)
             VALUES ($1, $2)
             ON CONFLICT DO NOTHING`,
            [profileId, tierId]
          );
        }
      }
    }

    console.log(`Seeded: ${user.username}`);
  }

  await client.end();
  console.log('Test user seeding complete.');
}

seed().catch(err => {
  console.error('Seeding error:', err);
  client.end();
});

