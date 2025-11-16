export default {
  routes: [
    {
      method: 'POST',
      path: '/route-depots/backfill-labels',
      handler: 'route-depot.backfillLabels',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/route-depots/debug-columns',
      handler: 'route-depot.debugColumns',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/route-depots',
      handler: 'route-depot.find',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/route-depots/:id',
      handler: 'route-depot.findOne',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/route-depots',
      handler: 'route-depot.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/route-depots/:id',
      handler: 'route-depot.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/route-depots/:id',
      handler: 'route-depot.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
  ],
};
