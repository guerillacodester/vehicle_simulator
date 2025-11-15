export default {
  routes: [
    {
      method: 'GET',
      path: '/services',
      handler: 'service.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/services/:id',
      handler: 'service.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/services',
      handler: 'service.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/services/:id',
      handler: 'service.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/services/:id',
      handler: 'service.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
        middlewares: [],
      },
    },
  ],
};