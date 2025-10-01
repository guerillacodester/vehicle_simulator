const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function checkLocaleSettings() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Check i18n locales
    console.log('\n=== I18N LOCALES ===');
    const localesResult = await client.query('SELECT * FROM i18n_locale ORDER BY id');
    console.log('Available locales:');
    localesResult.rows.forEach(locale => {
      console.log(`  ${locale.code}: ${locale.name} (default: ${locale.is_default})`);
    });

    // Check what locales our CMS data uses
    console.log('\n=== CMS DATA LOCALES ===');
    const tables = ['cms_drivers', 'cms_vehicles', 'cms_routes', 'cms_depots'];
    
    for (const table of tables) {
      const result = await client.query(`
        SELECT locale, COUNT(*) as count 
        FROM ${table} 
        GROUP BY locale 
        ORDER BY locale
      `);
      console.log(`${table}:`);
      result.rows.forEach(row => {
        console.log(`  ${row.locale}: ${row.count} records`);
      });
    }

    // Check if published_at is set correctly
    console.log('\n=== PUBLISHED STATUS ===');
    for (const table of tables) {
      const result = await client.query(`
        SELECT 
          COUNT(*) as total,
          COUNT(published_at) as published,
          COUNT(*) - COUNT(published_at) as drafts
        FROM ${table}
      `);
      const row = result.rows[0];
      console.log(`${table}: ${row.total} total, ${row.published} published, ${row.drafts} drafts`);
    }

    // Sample a few records to see their full structure
    console.log('\n=== SAMPLE DRIVER RECORD ===');
    const sampleDriver = await client.query('SELECT * FROM cms_drivers LIMIT 1');
    if (sampleDriver.rows.length > 0) {
      console.log(sampleDriver.rows[0]);
    }

  } catch (error) {
    console.error('❌ Check failed:', error.message);
    console.error(error.stack);
  } finally {
    await client.end();
  }
}

checkLocaleSettings();