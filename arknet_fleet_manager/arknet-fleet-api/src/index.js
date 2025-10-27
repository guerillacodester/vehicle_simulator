module.exports = {
  /**
   * An asynchronous register function that runs before
   * your application is initialized.
   *
   * This gives you an opportunity to extend code.
   */
  register(/*{ strapi }*/) {},

  /**
   * An asynchronous bootstrap function that runs before
   * your application gets started.
   *
   * This gives you an opportunity to set up your data model,
   * run jobs, or perform some special logic.
   */
  async bootstrap({ strapi }) {
    // Check if Route 1 spawn config already exists
    const route1Configs = await strapi.db.query('api::spawn-config.spawn-config').findMany({
      where: { name: 'Route 1 - St Lucy Rural' }
    });

    if (route1Configs.length > 0) {
      console.log('✅ Route 1 spawn config already exists');
      return;
    }

    console.log('🔧 Creating Route 1 - St Lucy Rural spawn config...');

    // Get template config
    const templateConfigs = await strapi.db.query('api::spawn-config.spawn-config').findMany({
      where: { name: 'Barbados Typical Weekday' },
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
      console.log('⚠️ Template config not found, skipping auto-creation');
      return;
    }

    const template = templateConfigs[0];

    // Get Route 1
    const routes = await strapi.db.query('api::route.route').findMany({
      where: { short_name: '1' }
    });

    if (!routes || routes.length === 0) {
      console.log('⚠️ Route 1 not found, skipping auto-creation');
      return;
    }

    // Adjust hourly rates for rural area
    const adjustedHourlyRates = template.hourly_spawn_rates.map(hr => ({
      hour: hr.hour,
      spawn_rate: 
        hr.hour === 4 ? 0.15 :
        hr.hour === 5 ? 0.4 :
        hr.hour === 6 ? 0.6 :   // 1.5 → 0.6
        hr.hour === 7 ? 1.2 :   // 2.8 → 1.2
        hr.hour === 8 ? 1.8 :
        hr.hour === 9 ? 1.2 :
        hr.hour === 12 ? 1.2 :
        hr.hour === 13 ? 1.2 :
        hr.hour === 17 ? 1.8 :
        hr.spawn_rate
    }));

    // Create new spawn config
    const newConfig = await strapi.db.query('api::spawn-config.spawn-config').create({
      data: {
        name: 'Route 1 - St Lucy Rural',
        description: 'Rural spawn configuration for Route 1 (St Lucy to St Peter) - Lower early morning rates suitable for rural areas',
        is_active: true,
        route: routes[0].id,
        building_weights: template.building_weights,
        poi_weights: template.poi_weights,
        landuse_weights: template.landuse_weights,
        hourly_spawn_rates: adjustedHourlyRates,
        day_multipliers: template.day_multipliers,
        distribution_params: template.distribution_params
      },
      populate: {
        building_weights: true,
        poi_weights: true,
        landuse_weights: true,
        hourly_spawn_rates: true,
        day_multipliers: true,
        distribution_params: true
      }
    });

    console.log(`✅ Created Route 1 spawn config (ID: ${newConfig.id})`);
    console.log(`   - ${newConfig.building_weights?.length || 0} building weights`);
    console.log(`   - ${newConfig.poi_weights?.length || 0} POI weights`);
    console.log(`   - ${newConfig.landuse_weights?.length || 0} landuse weights`);
    console.log(`   - ${newConfig.hourly_spawn_rates?.length || 0} hourly rates`);
    console.log(`   - ${newConfig.day_multipliers?.length || 0} day multipliers`);
    console.log(`   - Hour 6 rate: 0.6 (was 1.5)`);
    console.log(`   - Hour 7 rate: 1.2 (was 2.8)`);
  },
};
