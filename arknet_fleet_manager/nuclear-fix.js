const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5432,
  database: 'arknettransit',
  user: 'strapi',
  password: 'strapi123',
  ssl: false
});

async function nuclearFix() {
  try {
    await client.connect();
    console.log('🔗 Connected to database');
    
    console.log('🔥 NUCLEAR OPTION: Complete content reset');
    console.log('This will delete all imported content and let you recreate it properly');
    
    // First, get the current data to backup
    console.log('\n1️⃣ Backing up current data...');
    
    const backupData = {};
    
    // Backup vehicles
    const vehicles = await client.query('SELECT * FROM cms_vehicles ORDER BY id');
    backupData.vehicles = vehicles.rows.map(row => ({
      registration: row.registration,
      type: row.type,
      capacity: row.capacity,
      status: row.status
    }));
    
    // Backup drivers
    const drivers = await client.query('SELECT * FROM cms_drivers ORDER BY id');
    backupData.drivers = drivers.rows.map(row => ({
      name: row.name,
      license_number: row.license_number,
      status: row.status
    }));
    
    // Backup routes
    const routes = await client.query('SELECT * FROM cms_routes ORDER BY id');
    backupData.routes = routes.rows.map(row => ({
      code: row.code,
      name: row.name,
      geometry: row.geometry
    }));
    
    // Backup depots
    const depots = await client.query('SELECT * FROM cms_depots ORDER BY id');
    backupData.depots = depots.rows.map(row => ({
      name: row.name,
      location: row.location
    }));
    
    console.log(`✅ Backed up: ${backupData.vehicles.length} vehicles, ${backupData.drivers.length} drivers, ${backupData.routes.length} routes, ${backupData.depots.length} depots`);
    
    // Save backup to file
    const fs = require('fs');
    fs.writeFileSync('content-backup.json', JSON.stringify(backupData, null, 2));
    console.log('✅ Backup saved to content-backup.json');
    
    console.log('\n2️⃣ Clearing all imported content...');
    await client.query('DELETE FROM cms_vehicles');
    await client.query('DELETE FROM cms_drivers');
    await client.query('DELETE FROM cms_routes');
    await client.query('DELETE FROM cms_depots');
    console.log('✅ All content cleared');
    
    console.log('\n🎯 NOW DO THIS:');
    console.log('1. Refresh your admin panel - it should be empty');
    console.log('2. Create ONE vehicle manually using "Create new entry"');
    console.log('3. If that vehicle appears in the list, then we know the admin works');
    console.log('4. I\'ll then create a script to properly recreate all your data');
    
    console.log('\nSample vehicle to create:');
    console.log(`Registration: ${backupData.vehicles[0].registration}`);
    console.log(`Type: ${backupData.vehicles[0].type}`);
    console.log(`Capacity: ${backupData.vehicles[0].capacity}`);
    console.log(`Status: ${backupData.vehicles[0].status}`);
    
  } catch (error) {
    console.error('❌ Nuclear fix failed:', error.message);
  } finally {
    await client.end();
  }
}

nuclearFix();