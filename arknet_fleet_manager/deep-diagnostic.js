const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'strapi',
  password: 'strapi123',
  ssl: false
});

async function deepDiagnostic() {
  try {
    await client.connect();
    console.log('🔗 Connected to database');

    console.log('\n=== DEEP DIAGNOSTIC: WHY NO CONTENT IN ADMIN? ===\n');

    // 1. Check what Strapi's admin queries are actually returning
    console.log('1️⃣ Testing actual admin query for vehicles...');
    const adminQuery = `
      SELECT 
        id, 
        document_id, 
        registration, 
        type, 
        capacity, 
        status,
        created_at,
        updated_at,
        published_at,
        created_by_id,
        updated_by_id,
        locale
      FROM cms_vehicles 
      WHERE published_at IS NOT NULL
      ORDER BY registration ASC
      LIMIT 10
    `;
    
    const adminResult = await client.query(adminQuery);
    console.log(`✅ Query returned ${adminResult.rows.length} vehicles:`);
    adminResult.rows.forEach((row, index) => {
      console.log(`  ${index + 1}. ${row.registration} (${row.type}) - Locale: ${row.locale || 'NULL'}`);
    });

    // 2. Check locale configuration
    console.log('\n2️⃣ Checking locale issues...');
    const localeCheck = await client.query(`
      SELECT DISTINCT locale 
      FROM cms_vehicles 
      UNION 
      SELECT DISTINCT locale 
      FROM cms_drivers
      UNION
      SELECT DISTINCT locale 
      FROM cms_routes
      UNION
      SELECT DISTINCT locale 
      FROM cms_depots
    `);
    
    console.log('🌐 Locales found in data:');
    localeCheck.rows.forEach(row => {
      console.log(`  - ${row.locale || 'NULL'}`);
    });

    // 3. Check if there are any strapi_core_store settings that might affect this
    console.log('\n3️⃣ Checking Strapi core settings...');
    const coreSettings = await client.query(`
      SELECT key, value 
      FROM strapi_core_store_settings 
      WHERE key LIKE '%i18n%' OR key LIKE '%locale%' OR key LIKE '%content%'
      ORDER BY key
    `);
    
    if (coreSettings.rows.length > 0) {
      console.log('⚙️ Relevant core settings:');
      coreSettings.rows.forEach(row => {
        console.log(`  ${row.key}: ${row.value?.substring(0, 100)}...`);
      });
    } else {
      console.log('❌ No relevant core settings found');
    }

    // 4. Fix locale issue if found
    console.log('\n4️⃣ Fixing potential locale issues...');
    
    const tables = ['cms_vehicles', 'cms_drivers', 'cms_routes', 'cms_depots'];
    
    for (const table of tables) {
      const nullLocales = await client.query(`
        SELECT COUNT(*) as count 
        FROM ${table} 
        WHERE locale IS NULL
      `);
      
      if (nullLocales.rows[0].count > 0) {
        console.log(`🔧 Fixing ${nullLocales.rows[0].count} records with NULL locale in ${table}...`);
        await client.query(`
          UPDATE ${table} 
          SET locale = 'en', updated_at = NOW()
          WHERE locale IS NULL
        `);
        console.log(`✅ Updated ${table} with default 'en' locale`);
      } else {
        console.log(`✅ ${table} has no locale issues`);
      }
    }

    // 5. Check for any other obvious issues
    console.log('\n5️⃣ Final verification...');
    
    for (const table of tables) {
      const finalCheck = await client.query(`
        SELECT 
          COUNT(*) as total,
          COUNT(CASE WHEN published_at IS NOT NULL THEN 1 END) as published,
          COUNT(CASE WHEN created_by_id IS NOT NULL THEN 1 END) as has_creator,
          COUNT(CASE WHEN locale IS NOT NULL THEN 1 END) as has_locale
        FROM ${table}
      `);
      
      const stats = finalCheck.rows[0];
      console.log(`📊 ${table}: ${stats.total} total, ${stats.published} published, ${stats.has_creator} with creator, ${stats.has_locale} with locale`);
    }

    console.log('\n🎉 Diagnostic complete!');
    console.log('💡 Now try refreshing the admin panel and clearing browser cache...');

  } catch (error) {
    console.error('❌ Diagnostic failed:', error.message);
  } finally {
    await client.end();
  }
}

deepDiagnostic();