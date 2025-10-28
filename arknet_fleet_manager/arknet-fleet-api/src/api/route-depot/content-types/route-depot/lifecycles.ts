/**
 * Route-Depot Lifecycle Hooks
 * Auto-populate display_name field for better UI display
 */

export default {
  async beforeCreate(event: any) {
    const { data } = event.params;
    
    // Keep beforeCreate light; relations may not be resolved yet (docIds vs ids)
  },

  async beforeUpdate(event: any) {
    const { data } = event.params;
    
    try {
      // Load current record to determine changes
      const currentData = await strapi.entityService.findOne(
        'api::route-depot.route-depot' as any,
        event.params.where.id,
        { populate: ['depot', 'route'] }
      );

      if (currentData) {
        const depotId = data.depot !== undefined ? data.depot : (currentData as any).depot?.id;
        const routeId = data.route !== undefined ? data.route : (currentData as any).route?.id;

        // Refresh cached names if references changed or names missing
        if (depotId && (data.depot !== undefined || !data.depot_name)) {
          const depot = await strapi.entityService.findOne('api::depot.depot', depotId as any, {
            fields: ['name']
          });
          if (depot && (depot as any).name) {
            data.depot_name = (depot as any).name;
          }
        }

        if (routeId && (data.route !== undefined || !data.route_short_name)) {
          const route = await strapi.entityService.findOne('api::route.route', routeId as any, {
            fields: ['short_name']
          });
          if (route && (route as any).short_name) {
            data.route_short_name = (route as any).short_name;
          }
        }

        // Update display_name if depot or distance changed and display_name not explicitly provided
        if (data.display_name === undefined) {
          const effDepotName = data.depot_name ?? (currentData as any).depot_name;
          const effDistance = data.distance_from_route_m !== undefined
            ? data.distance_from_route_m
            : (currentData as any).distance_from_route_m;

          if (effDepotName && effDistance !== undefined) {
            const roundedDistance = Math.round(effDistance);
            data.display_name = `${effDepotName} - ${roundedDistance}m`;
          }
        }
      }
    } catch (error) {
      console.error('Failed to auto-update cached names/display for route-depot:', error);
    }
  }
  ,
  async afterCreate(event: any) {
    try {
      const createdId = event.result?.id;
      if (!createdId) return;
      const rec = await strapi.entityService.findOne('api::route-depot.route-depot' as any, createdId, {
        populate: {
          route: { fields: ['short_name'] },
          depot: { fields: ['name'] },
        },
      });
      const data: any = {};
      const routeShort = (rec as any)?.route_short_name ?? (rec as any)?.route?.short_name;
      const depotName = (rec as any)?.depot_name ?? (rec as any)?.depot?.name;
      if ((rec as any).route_short_name == null && routeShort) data.route_short_name = routeShort;
      if ((rec as any).depot_name == null && depotName) data.depot_name = depotName;
      if ((rec as any).display_name == null && depotName && (rec as any)?.distance_from_route_m !== undefined) {
        const rounded = Math.round((rec as any).distance_from_route_m);
        data.display_name = `${depotName} - ${rounded}m`;
      }
      if (Object.keys(data).length > 0) {
        await strapi.entityService.update('api::route-depot.route-depot' as any, createdId, { data });
      }
    } catch (error) {
      console.error('Failed in afterCreate to populate cached labels for route-depot:', error);
    }
  },
  async afterUpdate(event: any) {
    try {
      const updatedId = event.result?.id ?? event.params?.where?.id;
      if (!updatedId) return;
      const rec = await strapi.entityService.findOne('api::route-depot.route-depot' as any, updatedId, {
        populate: {
          route: { fields: ['short_name'] },
          depot: { fields: ['name'] },
        },
      });
      const data: any = {};
      const routeShort = (rec as any)?.route_short_name ?? (rec as any)?.route?.short_name;
      const depotName = (rec as any)?.depot_name ?? (rec as any)?.depot?.name;
      if ((rec as any).route_short_name == null && routeShort) data.route_short_name = routeShort;
      if ((rec as any).depot_name == null && depotName) data.depot_name = depotName;
      if ((rec as any).display_name == null && depotName && (rec as any)?.distance_from_route_m !== undefined) {
        const rounded = Math.round((rec as any).distance_from_route_m);
        data.display_name = `${depotName} - ${rounded}m`;
      }
      if (Object.keys(data).length > 0) {
        await strapi.entityService.update('api::route-depot.route-depot' as any, updatedId, { data });
      }
    } catch (error) {
      console.error('Failed in afterUpdate to populate cached labels for route-depot:', error);
    }
  }
};
