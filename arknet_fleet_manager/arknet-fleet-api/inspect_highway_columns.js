// Quick DB column inspector - run this with: node inspect_highway_columns.js
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

async function inspectColumns() {
  console.log('\n=== HIGHWAY_SHAPES TABLE COLUMNS ===');
  const shapeCols = await db.raw(`
    SELECT column_name, data_type 
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'highway_shapes'
    ORDER BY ordinal_position
  `);
  console.log(shapeCols.rows);

  console.log('\n=== HIGHWAY_SHAPES_HIGHWAY_LNK TABLE COLUMNS ===');
  const linkCols = await db.raw(`
    SELECT column_name, data_type 
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'highway_shapes_highway_lnk'
    ORDER BY ordinal_position
  `);
  console.log(linkCols.rows);

  console.log('\n=== CURRENT LINK TABLE DATA (SAMPLE) ===');
  const linkData = await db('highway_shapes_highway_lnk').limit(20);
  console.log(linkData);

  console.log('\n=== COUNTS ===');
  const highwayCount = await db('highways').count('* as count');
  const shapeCount = await db('highway_shapes').count('* as count');
  const linkCount = await db('highway_shapes_highway_lnk').count('* as count');
  console.log('Highways:', highwayCount[0].count);
  console.log('Highway Shapes:', shapeCount[0].count);
  console.log('Link Table Entries:', linkCount[0].count);

  await db.destroy();
}

inspectColumns().catch(console.error);
