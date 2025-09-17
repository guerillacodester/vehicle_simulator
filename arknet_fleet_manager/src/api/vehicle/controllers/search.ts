/**
 * Search controller - provides search endpoints for simulator compatibility
 */

export default {
  /**
   * Get vehicle-driver pairs (simulator expects this endpoint)
   */
  async vehicleDriverPairs(ctx) {
    try {
      // Get all vehicles with their relationships
      const vehicles = await strapi.entityService.findMany('api::vehicle.vehicle', {
        populate: {
          driver: true,
          route: true,
          depot: true
        }
      });

      // Get all drivers  
      const drivers = await strapi.entityService.findMany('api::driver.driver', {});

      // Format data for simulator compatibility
      const assignments = vehicles.map((vehicle: any) => ({
        vehicle_id: vehicle.id.toString(),
        vehicle_reg_code: vehicle.registration || `VEH-${vehicle.id}`,
        driver_id: vehicle.driver?.id?.toString() || null,
        driver_name: vehicle.driver?.name || 'Unassigned',
        route_id: vehicle.route?.id?.toString() || null,
        route_name: vehicle.route?.name || 'No Route',
        route_code: vehicle.route?.code || '0',
        status: vehicle.status || 'active',
        depot_name: vehicle.depot?.name || 'Main Depot'
      }));

      ctx.body = assignments;
    } catch (error) {
      console.error('Error in vehicleDriverPairs:', error);
      ctx.status = 500;
      ctx.body = { error: 'Internal server error' };
    }
  },

  /**
   * Get vehicles public endpoint
   */
  async vehiclesPublic(ctx) {
    try {
      const vehicles = await strapi.entityService.findMany('api::vehicle.vehicle', {
        populate: {
          driver: true,
          route: true,
          depot: true
        }
      });

      const formattedVehicles = vehicles.map((vehicle: any) => ({
        id: vehicle.id,
        registration: vehicle.registration,
        type: vehicle.type,
        capacity: vehicle.capacity,
        status: vehicle.status,
        driver: vehicle.driver ? {
          id: vehicle.driver.id,
          name: vehicle.driver.name,
          license_number: vehicle.driver.license_number
        } : null,
        route: vehicle.route ? {
          id: vehicle.route.id,
          code: vehicle.route.code,
          name: vehicle.route.name
        } : null,
        depot: vehicle.depot ? {
          id: vehicle.depot.id,
          name: vehicle.depot.name
        } : null
      }));

      ctx.body = formattedVehicles;
    } catch (error) {
      console.error('Error in vehiclesPublic:', error);
      ctx.status = 500;
      ctx.body = { error: 'Internal server error' };
    }
  },

  /**
   * Get route public by code
   */
  async routePublic(ctx) {
    try {
      const { code } = ctx.params;
      
      const routes = await strapi.entityService.findMany('api::route.route', {
        filters: { code: code },
        populate: '*',
      });

      if (!routes || routes.length === 0) {
        ctx.status = 404;
        ctx.body = { error: 'Route not found' };
        return;
      }

      const route: any = routes[0];
      ctx.body = {
        id: route.id,
        code: route.code,
        name: route.name,
        geometry: route.geometry ? JSON.parse(route.geometry) : null
      };
    } catch (error) {
      console.error('Error in routePublic:', error);
      ctx.status = 500;
      ctx.body = { error: 'Internal server error' };
    }
  },

  /**
   * Get route geometry by code
   */
  async routeGeometry(ctx) {
    try {
      const { code } = ctx.params;
      
      const routes = await strapi.entityService.findMany('api::route.route', {
        filters: { code: code },
      });

      if (!routes || routes.length === 0) {
        ctx.status = 404;
        ctx.body = { error: 'Route not found' };
        return;
      }

      const route: any = routes[0];
      const geometry = route.geometry ? JSON.parse(route.geometry) : null;
      
      if (!geometry) {
        ctx.status = 404;
        ctx.body = { error: 'Route geometry not found' };
        return;
      }

      ctx.body = geometry;
    } catch (error) {
      console.error('Error in routeGeometry:', error);
      ctx.status = 500;
      ctx.body = { error: 'Internal server error' };
    }
  }
};