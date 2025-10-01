/**
 * Simple script to set up public permissions via HTTP API
 */
const axios = require('axios');

const STRAPI_URL = 'http://localhost:1337';

async function setupPermissions() {
  try {
    console.log('🔧 Setting up basic permissions for simulator access...');
    
    // First, let's try to authenticate as admin to get access
    console.log('⚡ Trying to access public API endpoints...');
    
    // Test basic endpoints
    try {
      const response = await axios.get(`${STRAPI_URL}/api/vehicles`, {
        timeout: 5000
      });
      console.log('✅ Vehicles endpoint is accessible:', response.status);
    } catch (error) {
      console.log('❌ Vehicles endpoint is not accessible:', error.response?.status || error.message);
    }

    try {
      const response = await axios.get(`${STRAPI_URL}/api/drivers`, {
        timeout: 5000
      });
      console.log('✅ Drivers endpoint is accessible:', response.status);
    } catch (error) {
      console.log('❌ Drivers endpoint is not accessible:', error.response?.status || error.message);
    }

    try {
      const response = await axios.get(`${STRAPI_URL}/api/routes`, {
        timeout: 5000
      });
      console.log('✅ Routes endpoint is accessible:', response.status);
    } catch (error) {
      console.log('❌ Routes endpoint is not accessible:', error.response?.status || error.message);
    }

    console.log('\n📋 Next steps:');
    console.log('1. Go to http://localhost:1337/admin');
    console.log('2. Login with admin@arknet.com / AdminPassword123');
    console.log('3. Go to Settings > Users & Permissions plugin > Roles > Public');
    console.log('4. Enable permissions for Vehicle, Driver, Route, and Depot (find and findOne)');
    console.log('5. Save and test the simulator again');

  } catch (error) {
    console.error('❌ Error during setup:', error.message);
  }
}

if (require.main === module) {
  setupPermissions().catch(console.error);
}

module.exports = setupPermissions;