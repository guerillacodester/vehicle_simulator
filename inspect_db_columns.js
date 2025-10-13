const { Client } = require('pg');
(async ()=>{
  const client = new Client({
    host: 'localhost',
    port: 5432,
    database: 'arknettransit',
    user: 'postgres',
    password: process.env.PG_PASSWORD || 'postgres'
  });
  try{
    await client.connect();
    const res = await client.query(`SELECT column_name FROM information_schema.columns WHERE table_name='highways';`);
    console.log('columns for highways:', res.rows.map(r=>r.column_name));
    const res2 = await client.query(`SELECT column_name FROM information_schema.columns WHERE table_name='highway_shapes';`);
    console.log('columns for highway_shapes:', res2.rows.map(r=>r.column_name));
  }catch(e){
    console.error('error', e.message);
  }finally{await client.end();}
})();