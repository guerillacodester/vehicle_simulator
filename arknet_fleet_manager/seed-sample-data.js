/**
 * Seed sample data for testing the simulator integration
 */

const { execSync } = require('child_process');

// Sample route geometry (simple line between two points)
const sampleRouteGeometry = {
  "type": "LineString",
  "coordinates": [
    [-59.6463, 13.2810],
    [-59.6464, 13.2811],
    [-59.6465, 13.2812],
    [-59.6466, 13.2813]
  ]
};

const seedData = async () => {
  try {
    console.log('🌱 Starting data seeding...');
    
    // Create depot
    const depotPayload = {
      data: {
        name: "Main Depot",
        location: "Downtown Transit Center",
        publishedAt: new Date().toISOString()
      }
    };
    
    console.log('Creating depot...');
    const depotResponse = execSync(`curl -s -X POST http://localhost:1337/api/depots -H "Content-Type: application/json" -d '${JSON.stringify(depotPayload)}'`, { encoding: 'utf8' });
    const depot = JSON.parse(depotResponse);
    console.log('✅ Depot created:', depot.data?.attributes?.name);
    
    // Create driver
    const driverPayload = {
      data: {
        name: "John Driver",
        license_number: "DRV001",
        status: "active",
        publishedAt: new Date().toISOString()
      }
    };
    
    console.log('Creating driver...');
    const driverResponse = execSync(`curl -s -X POST http://localhost:1337/api/drivers -H "Content-Type: application/json" -d '${JSON.stringify(driverPayload)}'`, { encoding: 'utf8' });
    const driver = JSON.parse(driverResponse);
    console.log('✅ Driver created:', driver.data?.attributes?.name);
    
    // Create route
    const routePayload = {
      data: {
        code: "1",
        name: "Route 1 - Main Line",
        geometry: JSON.stringify(sampleRouteGeometry),
        publishedAt: new Date().toISOString()
      }
    };
    
    console.log('Creating route...');
    const routeResponse = execSync(`curl -s -X POST http://localhost:1337/api/routes -H "Content-Type: application/json" -d '${JSON.stringify(routePayload)}'`, { encoding: 'utf8' });
    const route = JSON.parse(routeResponse);
    console.log('✅ Route created:', route.data?.attributes?.name);
    
    // Create vehicle with relationships
    const vehiclePayload = {
      data: {
        registration: "ZR001",
        type: "bus",
        capacity: 40,
        status: "active",
        driver: driver.data?.id,
        route: route.data?.id,
        depot: depot.data?.id,
        publishedAt: new Date().toISOString()
      }
    };
    
    console.log('Creating vehicle...');
    const vehicleResponse = execSync(`curl -s -X POST http://localhost:1337/api/vehicles -H "Content-Type: application/json" -d '${JSON.stringify(vehiclePayload)}'`, { encoding: 'utf8' });
    const vehicle = JSON.parse(vehicleResponse);
    console.log('✅ Vehicle created:', vehicle.data?.attributes?.registration);
    
    console.log('\n🎉 Sample data seeding completed!');
    console.log('You can now test the simulator integration.');
    
  } catch (error) {
    console.error('❌ Error during seeding:', error.message);
    console.log('\n💡 Make sure Strapi is running and permissions are set up correctly.');
  }
};

if (require.main === module) {
  seedData().catch(console.error);
}

module.exports = seedData;