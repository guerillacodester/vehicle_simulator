/**
 * Automated script to duplicate spawn-config and adjust for Route 1
 * Run from Strapi project directory: node scripts/create_route1_config.js
 */

const Strapi = require('@strapi/strapi');

async function main() {
  const strapi = await Strapi.compile();
  await strapi.load();
  
  try {
  console.log('🔍 Finding template spawn-config...');
  
  // Get template config with all components populated
  const templateConfigs = await strapi.documents('api::spawn-config.spawn-config').findMany({
    filters: { name: 'Barbados Typical Weekday' },
    populate: {
      building_weights: true,
      poi_weights: true,
      landuse_weights: true,
      hourly_spawn_rates: true,
      day_multipliers: true,
      distribution_params: true
    }
  });
  
  if (!templateConfigs || templateConfigs.length === 0) {
    throw new Error('Template config not found');
  }
  
  const template = templateConfigs[0];
  console.log(`✅ Found template: ${template.name} (ID: ${template.id})`);
  console.log(`   Components: ${template.building_weights?.length || 0} buildings, ${template.hourly_spawn_rates?.length || 0} hourly rates`);
  
  // Get Route 1
  const routes = await strapi.documents('api::route.route').findMany({
    filters: { short_name: '1' }
  });
  
  if (!routes || routes.length === 0) {
    throw new Error('Route 1 not found');
  }
  
  const route1 = routes[0];
  console.log(`✅ Found Route 1 (ID: ${route1.documentId})`);
  
  // Adjust hourly rates for rural
  const adjustedHourlyRates = template.hourly_spawn_rates.map(hr => ({
    hour: hr.hour,
    spawn_rate: 
      hr.hour === 4 ? 0.15 :
      hr.hour === 5 ? 0.4 :
      hr.hour === 6 ? 0.6 :  // KEY: 1.5 → 0.6
      hr.hour === 7 ? 1.2 :  // KEY: 2.8 → 1.2
      hr.hour === 8 ? 1.8 :
      hr.hour === 9 ? 1.2 :
      hr.hour === 12 ? 1.2 :
      hr.hour === 13 ? 1.2 :
      hr.hour === 17 ? 1.8 :
      hr.spawn_rate
  }));
  
  console.log('\n📝 Creating Route 1 - St Lucy Rural config...');
  
  // Create new spawn-config with all components
  const newConfig = await strapi.documents('api::spawn-config.spawn-config').create({
    data: {
      name: 'Route 1 - St Lucy Rural',
      description: 'Rural spawn configuration for Route 1 (St Lucy to St Peter) - Lower early morning rates suitable for rural areas',
      is_active: true,
      building_weights: template.building_weights,
      poi_weights: template.poi_weights,
      landuse_weights: template.landuse_weights,
      hourly_spawn_rates: adjustedHourlyRates,
      day_multipliers: template.day_multipliers,
      distribution_params: template.distribution_params,
      route: route1.documentId
    }
  });
  
  console.log(`✅ Created spawn-config: ${newConfig.name} (ID: ${newConfig.id})`);
  console.log(`   Linked to Route: ${route1.short_name}`);
  
  // Publish it
  await strapi.documents('api::spawn-config.spawn-config').publish({
    documentId: newConfig.documentId
  });
  
  console.log('✅ Published spawn-config');
  
  console.log('\n' + '='.repeat(60));
  console.log('SUCCESS!');
  console.log(`Created Route 1 - St Lucy Rural (ID: ${newConfig.id})`);
  console.log('  Hour 6 rate: 0.6 (was 1.5)');
  console.log('  Hour 7 rate: 1.2 (was 2.8)');
  console.log('  Expected spawns at 6 AM: ~16 passengers (was 48)');
  console.log('='.repeat(60));
  
  } catch (error) {
    console.error('❌ ERROR:', error.message);
    console.error(error);
    process.exit(1);
  } finally {
    await strapi.destroy();
    process.exit(0);
  }
}

main();
