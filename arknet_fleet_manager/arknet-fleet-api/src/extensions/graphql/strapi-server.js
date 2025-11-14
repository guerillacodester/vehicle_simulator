const routeGeometryResolver = require('./routeGeometry/resolvers/routeGeometry');

module.exports = (plugin) => {
  const extensionService = plugin.service('extension');

  extensionService.use(({ nexus, strapi }) => ({
    resolversConfig: {
      'Query.routeGeometry': {
        auth: false,
        policies: [],
      },
    },
    types: [
      ...routeGeometryResolver({ nexus, strapi }),
    ],
  }));

  return plugin;
};
