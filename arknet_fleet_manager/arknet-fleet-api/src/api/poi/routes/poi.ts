export default {
  routes: [
    {
      method: 'GET',
      path: '/pois',
      handler: 'poi.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/pois/:id',
      handler: 'poi.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/pois',
      handler: 'poi.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/pois/:id',
      handler: 'poi.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/pois/:id',
      handler: 'poi.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
        middlewares: [],
      },
    },
  ],
};
