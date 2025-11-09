import { factories } from '@strapi/strapi';

export default factories.createCoreController('api::route.route', ({ strapi }) => ({
  // Override find to return list with basic info
  async find(ctx) {
    const { data, meta } = await super.find(ctx);
    
    // Transform to simple format for list view
    const routes = data.map((item: any) => ({
      id: item.id,
      attributes: {
        code: item.attributes.short_name,
        name: item.attributes.long_name || item.attributes.short_name,
        origin: item.attributes.parishes?.split(',')[0]?.trim() || '',
        destination: item.attributes.parishes?.split(',')[1]?.trim() || '',
        color: item.attributes.color,
      }
    }));
    
    return { data: routes, meta };
  },

  // Override findOne to include GTFS-compliant stops and shapes
  async findOne(ctx) {
    const { id } = ctx.params;
    
    // Get route with trips
    const route: any = await strapi.entityService.findOne('api::route.route', id, {
      populate: ['trips']
    });
    
    if (!route) {
      return ctx.notFound('Route not found');
    }
    
    // Get a representative trip (first active trip)
    const trips: any[] = route.trips || [];
    const representativeTripId = trips.find((t: any) => t.id)?.id;
    
    let stops: any[] = [];
    let shapePoints: any[] = [];
    
    if (representativeTripId) {
      // Get stop_times for this trip with stop details
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
      
      // Get shape from trip
      const trip: any = await strapi.entityService.findOne('api::trip.trip', representativeTripId, {
        populate: ['shape']
      });
      
      if (trip?.shape) {
        // Get all shape points
        const shapes: any = await strapi.entityService.findMany('api::shape.shape' as any, {
          filters: { shape_id: trip.shape.shape_id },
          sort: ['shape_pt_sequence:asc']
        });
        
        shapePoints = shapes.map((s: any) => [
          parseFloat(s.shape_pt_lon),
          parseFloat(s.shape_pt_lat)
        ]);
      }
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