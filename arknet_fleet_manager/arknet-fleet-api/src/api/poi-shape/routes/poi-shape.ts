export default {
  routes: [
    {
      method: 'GET',
      path: '/poi-shapes',
      handler: 'poi-shape.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/poi-shapes/:id',
      handler: 'poi-shape.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'viewer' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/poi-shapes',
      handler: 'poi-shape.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/poi-shapes/:id',
      handler: 'poi-shape.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'operator' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/poi-shapes/:id',
      handler: 'poi-shape.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'manager' } }],
        middlewares: [],
      },
    },
  ],
};
