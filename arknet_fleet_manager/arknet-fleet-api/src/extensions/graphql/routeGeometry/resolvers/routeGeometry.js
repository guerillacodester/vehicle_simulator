module.exports = ({ nexus, strapi }) => [
  // Define RouteMetrics type
  nexus.objectType({
    name: 'RouteMetrics',
    definition(t) {
      t.nonNull.int('totalPoints');
      t.nonNull.float('estimatedLengthKm');
      t.nonNull.int('segments');
      t.nonNull.int('reversedCount');
    },
  }),

  // Define RouteGeometryResponse type
  nexus.objectType({
    name: 'RouteGeometryResponse',
    definition(t) {
      t.nonNull.boolean('success');
      t.nonNull.string('routeName');
      t.field('metrics', { type: 'RouteMetrics' });
      t.nonNull.int('coordinateCount');
      t.nonNull.int('segmentCount');
      t.nonNull.float('distanceKm');
      t.list.field('coordinates', { type: 'JSON' });
    },
  }),

  // Extend Query type with routeGeometry field
  nexus.extendType({
    type: 'Query',
    definition(t) {
      t.field('routeGeometry', {
        type: 'RouteGeometryResponse',
        args: {
          routeName: nexus.nonNull(nexus.stringArg()),
        },
        async resolve(_root, args) {
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
            distanceKm: Number(result.metrics.estimatedLengthKm),
          };
        },
      });
    },
  }),
];
