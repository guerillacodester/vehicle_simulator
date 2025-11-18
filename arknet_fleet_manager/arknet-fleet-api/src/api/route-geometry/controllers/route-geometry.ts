/**
 * Standalone route geometry controller
 * Bypasses users-permissions by not being part of a content-type
 */

export default {
  async getGeometry(ctx: any) {
    strapi.log.info(`[route-geometry] Handler called for routeName=${ctx.params.routeName}, user=${ctx.state.user?.username}`);
    
    // Call the original route service method
    try {
      const routeService = strapi.service('api::route.route');
      const result = await routeService.fetchRouteGeometry(ctx.params.routeName);
      
      ctx.body = {
        success: true,
        routeName: ctx.params.routeName,
        metrics: result.metrics,
        coordinateCount: result.coords.length,
        segmentCount: result.segments.length,
        coordinates: result.coords,
        distanceKm: Number(result.metrics.estimatedLengthKm),
      };
    } catch (error) {
      ctx.status = 500;
      ctx.body = {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  },
};
