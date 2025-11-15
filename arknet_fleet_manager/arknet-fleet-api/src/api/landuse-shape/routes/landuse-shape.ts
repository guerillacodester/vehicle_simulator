export default {
  routes: [
    {
      method: 'GET',
      path: '/landuse-shapes',
      handler: 'landuse-shape.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/landuse-shapes/:id',
      handler: 'landuse-shape.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/landuse-shapes',
      handler: 'landuse-shape.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: {} }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/landuse-shapes/:id',
      handler: 'landuse-shape.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: {} }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/landuse-shapes/:id',
      handler: 'landuse-shape.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: {} }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};
