const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'strapi',
  password: 'strapi123',
  ssl: false
});

async function syncStrapiData() {
  try {
    await client.connect();
    console.log('🔗 Connected to database');

    // The issue might be that Strapi expects certain metadata fields
    // Let's check what's actually in the database vs what Strapi expects

    console.log('\n📊 Checking current data structure...');

    const tables = [
      { name: 'cms_vehicles', api: 'vehicle' },
      { name: 'cms_drivers', api: 'driver' },
      { name: 'cms_routes', api: 'route' },
      { name: 'cms_depots', api: 'depot' }
    ];

    for (const table of tables) {
      console.log(`\n=== ${table.name.toUpperCase()} ===`);
      
      // Check table structure
      const structureResult = await client.query(`
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns 
        WHERE table_name = $1 
        ORDER BY ordinal_position
      `, [table.name]);

      console.log('📋 Table structure:');
      structureResult.rows.forEach(col => {
        console.log(`  ${col.column_name}: ${col.data_type} ${col.is_nullable === 'NO' ? '(NOT NULL)' : ''}`);
      });

      // Check actual data
      const dataResult = await client.query(`
        SELECT 
          id, 
          document_id, 
          created_at, 
          updated_at, 
          published_at,
          created_by_id,
          updated_by_id
        FROM ${table.name} 
        ORDER BY id
      `);

      console.log(`\n📦 Found ${dataResult.rows.length} records:`);
      dataResult.rows.forEach((row, index) => {
        const status = row.published_at ? '✅ Published' : '❌ Draft';
        const creator = row.created_by_id || 'NULL';
        const updater = row.updated_by_id || 'NULL';
        console.log(`  ${index + 1}. ID: ${row.id}, Doc: ${row.document_id?.substring(0, 8)}..., Creator: ${creator}, ${status}`);
      });

      // Fix missing creator/updater references (this might be the issue!)
      const missingCreatorCount = dataResult.rows.filter(row => !row.created_by_id).length;
      if (missingCreatorCount > 0) {
        console.log(`\n⚠️  ${missingCreatorCount} records missing created_by_id. Let's check if we have admin users...`);
        
        // Check for admin users
        const adminResult = await client.query(`
          SELECT id, firstname, lastname, username, email 
          FROM admin_users 
          ORDER BY id 
          LIMIT 5
        `);

        if (adminResult.rows.length > 0) {
          const adminId = adminResult.rows[0].id;
          console.log(`👤 Found admin user: ${adminResult.rows[0].firstname} ${adminResult.rows[0].lastname} (ID: ${adminId})`);
          console.log(`🔧 Updating records to reference admin user...`);

          await client.query(`
            UPDATE ${table.name} 
            SET 
              created_by_id = $1, 
              updated_by_id = $1,
              updated_at = NOW()
            WHERE created_by_id IS NULL
          `, [adminId]);

          console.log(`✅ Updated ${missingCreatorCount} records with admin user reference`);
        } else {
          console.log('❌ No admin users found - this might be the problem!');
        }
      }
    }

    console.log('\n🎉 Data synchronization check complete!');
    console.log('💡 Try refreshing the admin panel now...');

  } catch (error) {
    console.error('❌ Sync failed:', error.message);
  } finally {
    await client.end();
  }
}

syncStrapiData();