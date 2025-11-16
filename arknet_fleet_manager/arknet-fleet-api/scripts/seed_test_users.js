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
  { username: 'superadmin_user', email: 'superadmin@test.com', password: 'Test123!', tier: 'SuperAdmin' },
  { username: 'admin_user', email: 'admin@test.com', password: 'Test123!', tier: 'Admin' },
  { username: 'manager_user', email: 'manager@test.com', password: 'Test123!', tier: 'Manager' },
  { username: 'dispatcher_user', email: 'dispatcher@test.com', password: 'Test123!', tier: 'Dispatcher' },
  { username: 'operator_user', email: 'operator@test.com', password: 'Test123!', tier: 'Operator' },
  { username: 'viewer_user', email: 'viewer@test.com', password: 'Test123!', tier: 'Viewer' },
  { username: 'guest_user', email: 'guest@test.com', password: 'Test123!', tier: 'Guest' }
];

async function seed() {
  await client.connect();

  for (const user of users) {
    // Hash the password
    const hashedPassword = await bcrypt.hash(user.password, 10);

    // Check if user exists
    let userId;
    const existingUser = await client.query(
      `SELECT id FROM up_users WHERE username = $1`,
      [user.username]
    );
    
    if (existingUser.rows.length > 0) {
      userId = existingUser.rows[0].id;
      // Update password
      await client.query(
        `UPDATE up_users SET password = $1, email = $2, updated_at = NOW() WHERE id = $3`,
        [hashedPassword, user.email, userId]
      );
      console.log(`Updated existing user: ${user.username}`);
    } else {
      // Insert user
      const userRes = await client.query(
        `INSERT INTO up_users (username, email, password, provider, confirmed, blocked, created_at, updated_at)
         VALUES ($1, $2, $3, 'local', true, false, NOW(), NOW())
         RETURNING id`,
        [user.username, user.email, hashedPassword]
      );
      userId = userRes.rows[0].id;
      console.log(`Created new user: ${user.username}`);
    }

    // Check if profile exists for this user (via join table)
    let profileId;
    const existingLink = await client.query(
      `SELECT user_profile_id FROM user_profiles_user_lnk WHERE user_id = $1`,
      [userId]
    );
    
    if (existingLink.rows.length > 0) {
      profileId = existingLink.rows[0].user_profile_id;
    } else {
      // Create user profile
      const profileRes = await client.query(
        `INSERT INTO user_profiles (created_at, updated_at, published_at)
         VALUES (NOW(), NOW(), NOW())
         RETURNING id`,
        []
      );
      profileId = profileRes.rows[0].id;
      
      // Link user to profile
      await client.query(
        `INSERT INTO user_profiles_user_lnk (user_profile_id, user_id)
         VALUES ($1, $2)`,
        [profileId, userId]
      );
    }

    // Get tier id
    const tierRes = await client.query(
      `SELECT id FROM access_tiers WHERE name = $1`,
      [user.tier]
    );

    if (tierRes.rows.length > 0) {
      const tierId = tierRes.rows[0].id;

      // Delete existing link first, then insert
      await client.query(
        `DELETE FROM user_profiles_access_tier_lnk WHERE user_profile_id = $1`,
        [profileId]
      );
      
      await client.query(
        `INSERT INTO user_profiles_access_tier_lnk (user_profile_id, access_tier_id)
         VALUES ($1, $2)`,
        [profileId, tierId]
      );
      
      console.log(`✓ Seeded: ${user.username} (${user.tier})`);
    } else {
      console.log(`✗ Warning: Tier '${user.tier}' not found for user ${user.username}`);
    }
  }

  await client.end();
  console.log('Test user seeding complete.');
}

seed().catch(err => {
  console.error('Seeding error:', err);
  client.end();
});

