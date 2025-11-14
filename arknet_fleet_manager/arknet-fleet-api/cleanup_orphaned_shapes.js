// Clean up orphaned highway shapes
const knex = require('knex');

const db = knex({
  client: 'pg',
  connection: {
    host: '127.0.0.1',
    port: 5432,
    user: 'david',
    password: 'Ga25w123!',
    database: 'arknettransit'
  }
});

async function cleanup() {
  console.log('\n=== CLEANING UP ORPHANED HIGHWAY SHAPES ===');
  
  const deleted = await db('highway_shapes').del();
  console.log(`Deleted ${deleted} orphaned shapes`);
  
  await db.destroy();
  process.exit(0);
}

cleanup().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
