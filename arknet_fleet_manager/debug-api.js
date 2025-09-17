const axios = require('axios');

// First, let's get the data from the API to make sure it's there
async function recreateViaStrapi() {
  try {
    console.log('🔄 Recreating content via Strapi API...');
    
    // Get current data from API
    console.log('1️⃣ Getting current data from API...');
    const vehiclesResponse = await axios.get('http://localhost:1337/api/vehicles');
    const driversResponse = await axios.get('http://localhost:1337/api/drivers');
    const routesResponse = await axios.get('http://localhost:1337/api/routes');
    const depotsResponse = await axios.get('http://localhost:1337/api/depots');
    
    console.log(`✅ API returns: ${vehiclesResponse.data.data.length} vehicles, ${driversResponse.data.data.length} drivers, ${routesResponse.data.data.length} routes, ${depotsResponse.data.data.length} depots`);
    
    if (vehiclesResponse.data.data.length === 0) {
      console.log('❌ API returns no vehicles - something is very wrong!');
      return;
    }
    
    console.log('2️⃣ Sample vehicle from API:');
    console.log(JSON.stringify(vehiclesResponse.data.data[0], null, 2));
    
    // The problem might be that we need to delete and recreate using Strapi's method
    console.log('\n🔥 NUCLEAR OPTION: Delete all and recreate via API...');
    console.log('This will use Strapi\'s internal methods instead of direct DB inserts');
    
    // We need admin authentication to use the content-manager API
    console.log('\n⚠️  We need to authenticate as admin to use content-manager API');
    console.log('💡 Try this: Create one vehicle manually in the admin panel');
    console.log('   Then check if it appears alongside the others');
    
  } catch (error) {
    console.error('❌ Failed:', error.message);
    if (error.response) {
      console.error('Response:', error.response.status, error.response.data);
    }
  }
}

recreateViaStrapi();