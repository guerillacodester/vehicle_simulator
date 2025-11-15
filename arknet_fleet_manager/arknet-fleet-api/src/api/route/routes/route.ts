export default {
  routes: [
    {
      method: 'GET',
      path: '/routes',
      handler: 'route.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/routes/:id',
      handler: 'route.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/routes',
      handler: 'route.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/routes/:id',
      handler: 'route.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/routes/:id',
      handler: 'route.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/routes/:routeName/geometry',
      handler: 'route.getGeometry',
      config: {
        auth: { scope: ['admin'] },
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
  ],
};