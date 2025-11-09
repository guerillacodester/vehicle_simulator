module.exports = ({ strapi }: any) => {
  const extensionService = strapi.plugin('graphql').service('extension');

  extensionService.use(({ nexus }: any) => ({
    types: [
      nexus.extendType({
        type: 'Query',
        definition(t: any) {
          t.field('routeGeometry', {
            type: 'RouteGeometryResponse',
            args: {
              routeName: nexus.nonNull(nexus.stringArg()),
            },
            async resolve(_root: any, args: any) {
              const { routeName } = args;
              const result = await strapi
                .service('api::route.route')
                .fetchRouteGeometry(routeName);

              return {
                success: true,
                routeName,
                metrics: result.metrics,
                coordinateCount: result.coords.length,
                segmentCount: result.segments.length,
                coordinates: result.coords,
              };
            },
          });
        },
      }),
      
      nexus.objectType({
        name: 'RouteGeometryResponse',
        definition(t: any) {
          t.nonNull.boolean('success');
          t.nonNull.string('routeName');
          t.field('metrics', { type: 'RouteMetrics' });
          t.nonNull.int('coordinateCount');
          t.nonNull.int('segmentCount');
          t.list.field('coordinates', {
            type: 'JSON',
          });
        },
      }),
      
      nexus.objectType({
        name: 'RouteMetrics',
        definition(t: any) {
          t.nonNull.int('totalPoints');
          t.nonNull.float('estimatedLengthKm');
          t.nonNull.int('segments');
          t.nonNull.int('reversedCount');
        },
      }),
    ],
  }));
};
