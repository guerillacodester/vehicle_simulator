require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const { Client } = require('pg');
(async () => {
  const client = new Client({
    host: process.env.DATABASE_HOST, port: Number(process.env.DATABASE_PORT), database: process.env.DATABASE_NAME,
    user: process.env.DATABASE_USERNAME, password: process.env.DATABASE_PASSWORD,
  });
  try {
    await client.connect();
    const r = await client.query("SELECT schemaname, tablename FROM pg_tables WHERE tablename ILIKE '%user%permission%' OR tablename ILIKE '%users%' OR tablename ILIKE '%plugin_users%' ORDER BY tablename");
    console.log('Found tables:', r.rows.length);
    console.table(r.rows);
    await client.end();
  } catch (ERR) {
    console.error('Failed to query:', ERR);
    process.exit(1);
  }
})();
