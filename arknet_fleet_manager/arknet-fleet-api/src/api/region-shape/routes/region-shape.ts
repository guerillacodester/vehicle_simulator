export default {
  routes: [
    {
      method: 'GET',
      path: '/region-shapes',
      handler: 'region-shape.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/region-shapes/:id',
      handler: 'region-shape.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/region-shapes',
      handler: 'region-shape.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/region-shapes/:id',
      handler: 'region-shape.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/region-shapes/:id',
      handler: 'region-shape.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
  ],
};
