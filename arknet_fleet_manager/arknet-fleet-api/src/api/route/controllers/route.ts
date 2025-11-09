import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::route.route', ({ strapi }) => ({
  // Override find to return list with basic info
  async find(ctx) {
    const { data, meta } = await super.find(ctx);
    
    // Transform to simple format for list view (defensive)
    const routes = (data || []).map((item: any) => {
      const attrs = (item && item.attributes) || {};
      const parishes = attrs.parishes || '';
      const parts = String(parishes).split(',');
      return {
        id: item && item.id,
        attributes: {
          code: attrs.short_name || attrs.code || '',
          name: attrs.long_name || attrs.short_name || attrs.name || '',
          origin: (parts[0] || '').trim(),
          destination: (parts[1] || '').trim(),
          color: attrs.color || ''
        }
      };
    });
    
    return { data: routes, meta };
  },

  // Override findOne to include GTFS-compliant stops and shapes
  async findOne(ctx) {
    const { id } = ctx.params;
    
    // Get route
    const route: any = await strapi.entityService.findOne('api::route.route', id, {
      populate: ['trips']
    });
    
    if (!route) {
      return ctx.notFound('Route not found');
    }
    
    // Use short_name as route_id for route_shapes lookup
    const routeId = route.short_name || String(route.id);
    
    let stops: any[] = [];
    let shapePoints: any[] = [];
    
    // Find DEFAULT route_shape for this route (NOT all variants!)
    const routeShapes: any = await strapi.entityService.findMany('api::route-shape.route-shape' as any, {
      filters: { 
        route_id: routeId,
        is_default: true  // ONLY get the default shape
      }
    });
    
    if (routeShapes && routeShapes.length > 0) {
      // Get the default shape_id
      const defaultShapeId = routeShapes[0].shape_id;
      
      // Get shape points for ONLY the default shape
      const shapes: any = await strapi.entityService.findMany('api::shape.shape' as any, {
        filters: { shape_id: defaultShapeId },
        sort: ['shape_pt_sequence:asc'],
        pagination: { pageSize: 10000 }
      });
      
      shapePoints = shapes.map((s: any) => [
        parseFloat(s.shape_pt_lon),
        parseFloat(s.shape_pt_lat)
      ]);
    }
    
    // Get stops from trips if available
    const trips: any[] = route.trips || [];
    const representativeTripId = trips.find((t: any) => t.id)?.id;
    
    if (representativeTripId) {
      const stopTimes: any = await strapi.entityService.findMany('api::stop-time.stop-time' as any, {
        filters: { trip: representativeTripId },
        populate: ['stop'],
        sort: ['stop_sequence:asc']
      });
      
      stops = stopTimes.map((st: any) => ({
        id: st.stop?.stop_id || st.stop?.id,
        name: st.stop?.name || '',
        lat: parseFloat(st.stop?.latitude || 0),
        lon: parseFloat(st.stop?.longitude || 0),
        sequence: st.stop_sequence
      }));
    }
    
    return {
      data: {
        id: route.id,
        attributes: {
          code: route.short_name,
          name: route.long_name || route.short_name,
          origin: route.parishes?.split(',')[0]?.trim() || '',
          destination: route.parishes?.split(',')[1]?.trim() || '',
          color: route.color,
          stops: stops,
          geometry: shapePoints.length > 0 ? {
            type: 'LineString',
            coordinates: shapePoints
          } : null
        }
      }
    };
  }
}));