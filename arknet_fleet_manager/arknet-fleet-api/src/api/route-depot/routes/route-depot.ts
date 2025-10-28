export default {
  routes: [
    {
      method: 'GET',
      path: '/route-depots',
      handler: 'route-depot.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/route-depots/:id',
      handler: 'route-depot.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/route-depots',
      handler: 'route-depot.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/route-depots/:id',
      handler: 'route-depot.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/route-depots/:id',
      handler: 'route-depot.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
