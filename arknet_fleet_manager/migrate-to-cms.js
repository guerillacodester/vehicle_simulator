const { Client } = require('pg');

const client = new Client({
  host: '127.0.0.1',
  port: 5433,
  database: 'arknettransit',
  user: 'david',
  password: 'Ga25w123!',
  ssl: false
});

async function migrateData() {
  try {
    await client.connect();
    console.log('Connected to database');

    // Check existing data in legacy tables
    console.log('\n=== Checking legacy tables ===');
    
    const driversResult = await client.query('SELECT * FROM drivers ORDER BY driver_id');
    console.log(`Found ${driversResult.rows.length} drivers in legacy table`);
    
    const vehiclesResult = await client.query('SELECT * FROM vehicles ORDER BY vehicle_id');
    console.log(`Found ${vehiclesResult.rows.length} vehicles in legacy table`);
    
    const routesResult = await client.query('SELECT * FROM routes ORDER BY route_id');
    console.log(`Found ${routesResult.rows.length} routes in legacy table`);
    
    const depotsResult = await client.query('SELECT * FROM depots ORDER BY depot_id');
    console.log(`Found ${depotsResult.rows.length} depots in legacy table`);

    // Clear existing CMS tables first
    console.log('\n=== Clearing existing CMS data ===');
    await client.query('DELETE FROM cms_drivers');
    await client.query('DELETE FROM cms_vehicles');
    await client.query('DELETE FROM cms_routes');
    await client.query('DELETE FROM cms_depots');
    console.log('Cleared all CMS tables');

    // Migrate drivers
    console.log('\n=== Migrating drivers ===');
    for (const driver of driversResult.rows) {
      await client.query(`
        INSERT INTO cms_drivers (name, license_number, status, published_at, created_at, updated_at, locale)
        VALUES ($1, $2, $3, NOW(), NOW(), NOW(), 'en')
      `, [
        driver.name,
        driver.license_no,
        driver.employment_status || 'active'
      ]);
      console.log(`✓ Migrated driver: ${driver.name}`);
    }

    // Migrate vehicles
    console.log('\n=== Migrating vehicles ===');
    for (const vehicle of vehiclesResult.rows) {
      await client.query(`
        INSERT INTO cms_vehicles (registration, type, capacity, status, published_at, created_at, updated_at, locale)
        VALUES ($1, $2, $3, $4, NOW(), NOW(), NOW(), 'en')
      `, [
        vehicle.reg_code,
        'bus', // Default type since legacy table uses different enum
        vehicle.capacity || 16,
        vehicle.status || 'active'
      ]);
      console.log(`✓ Migrated vehicle: ${vehicle.reg_code}`);
    }

    // Migrate routes
    console.log('\n=== Migrating routes ===');
    for (const route of routesResult.rows) {
      await client.query(`
        INSERT INTO cms_routes (code, name, geometry, published_at, created_at, updated_at, locale)
        VALUES ($1, $2, $3, NOW(), NOW(), NOW(), 'en')
      `, [
        route.short_name,
        route.long_name || route.short_name,
        null // No geometry in legacy table
      ]);
      console.log(`✓ Migrated route: ${route.short_name} - ${route.long_name}`);
    }

    // Migrate depots
    console.log('\n=== Migrating depots ===');
    for (const depot of depotsResult.rows) {
      await client.query(`
        INSERT INTO cms_depots (name, location, published_at, created_at, updated_at, locale)
        VALUES ($1, $2, NOW(), NOW(), NOW(), 'en')
      `, [
        depot.name,
        depot.location ? depot.location.toString() : null
      ]);
      console.log(`✓ Migrated depot: ${depot.name}`);
    }

    // Verify migration
    console.log('\n=== Verifying migration ===');
    const cmsDrivers = await client.query('SELECT COUNT(*) FROM cms_drivers');
    const cmsVehicles = await client.query('SELECT COUNT(*) FROM cms_vehicles');
    const cmsRoutes = await client.query('SELECT COUNT(*) FROM cms_routes');
    const cmsDepots = await client.query('SELECT COUNT(*) FROM cms_depots');

    console.log(`CMS Drivers: ${cmsDrivers.rows[0].count}`);
    console.log(`CMS Vehicles: ${cmsVehicles.rows[0].count}`);
    console.log(`CMS Routes: ${cmsRoutes.rows[0].count}`);
    console.log(`CMS Depots: ${cmsDepots.rows[0].count}`);

    console.log('\n✅ Migration completed successfully!');

  } catch (error) {
    console.error('❌ Migration failed:', error.message);
    console.error(error.stack);
  } finally {
    await client.end();
  }
}

migrateData();