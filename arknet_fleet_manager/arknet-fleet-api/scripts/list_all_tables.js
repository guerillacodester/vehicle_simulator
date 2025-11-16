require('dotenv').config({ path: require('path').join(__dirname, '../.env') });
const { Client } = require('pg');
(async () => {
  const client = new Client({
    host: process.env.DATABASE_HOST, port: Number(process.env.DATABASE_PORT), database: process.env.DATABASE_NAME,
    user: process.env.DATABASE_USERNAME, password: process.env.DATABASE_PASSWORD,
  });
  await client.connect();
  const r = await client.query("SELECT schemaname, tablename FROM pg_tables WHERE schemaname NOT IN ('pg_catalog','information_schema') ORDER BY schemaname, tablename");
  console.log('Tables total', r.rows.length);
  console.table(r.rows);
  await client.end();
})();
