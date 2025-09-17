export default {
  routes: [
    {
      method: 'GET',
      path: '/depots',
      handler: 'depot.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/depots/:id',
      handler: 'depot.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/depots',
      handler: 'depot.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/depots/:id',
      handler: 'depot.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/depots/:id',
      handler: 'depot.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};