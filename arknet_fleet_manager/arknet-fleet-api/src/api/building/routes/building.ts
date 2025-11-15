export default {
  routes: [
    {
      method: 'GET',
      path: '/buildings',
      handler: 'building.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/buildings/:id',
      handler: 'building.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/buildings',
      handler: 'building.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/buildings/:id',
      handler: 'building.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/buildings/:id',
      handler: 'building.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
  ],
};
