export default {
  routes: [
    {
      method: 'GET',
      path: '/places',
      handler: 'place.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/places/:id',
      handler: 'place.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/places',
      handler: 'place.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/places/:id',
      handler: 'place.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/places/:id',
      handler: 'place.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};
