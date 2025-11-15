export default {
  routes: [
    {
      method: 'GET',
      path: '/shapes',
      handler: 'shape.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/shapes/:id',
      handler: 'shape.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/shapes',
      handler: 'shape.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/shapes/:id',
      handler: 'shape.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/shapes/:id',
      handler: 'shape.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
        middlewares: [],
      },
    },
  ],
};