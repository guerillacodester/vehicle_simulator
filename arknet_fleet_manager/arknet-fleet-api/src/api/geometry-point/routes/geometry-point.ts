export default {
  routes: [
    {
      method: 'GET',
      path: '/geometry-points',
      handler: 'geometry-point.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/geometry-points/:id',
      handler: 'geometry-point.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/geometry-points',
      handler: 'geometry-point.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/geometry-points/:id',
      handler: 'geometry-point.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/geometry-points/:id',
      handler: 'geometry-point.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};
