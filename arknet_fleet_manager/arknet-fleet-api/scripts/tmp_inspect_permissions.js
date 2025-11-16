require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const { Client } = require('pg');

async function main() {
  const client = new Client({
    host: process.env.DATABASE_HOST,
    port: Number(process.env.DATABASE_PORT || 5432),
    user: process.env.DATABASE_USERNAME,
    password: process.env.DATABASE_PASSWORD,
    database: process.env.DATABASE_NAME,
  });

  await client.connect();
  const perms = await client.query(
    "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'up_permissions' ORDER BY ordinal_position"
  );
  console.log('up_permissions columns:', perms.rows);

  const links = await client.query(
    "SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'up_permissions_role_lnk' ORDER BY ordinal_position"
  );
  console.log('up_permissions_role_lnk columns:', links.rows);
  await client.end();
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
