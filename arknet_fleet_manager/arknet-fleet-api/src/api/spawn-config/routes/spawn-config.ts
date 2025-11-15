export default {
  routes: [
    {
      method: 'GET',
      path: '/spawn-configs',
      handler: 'spawn-config.find',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/spawn-configs/:id',
      handler: 'spawn-config.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/spawn-configs',
      handler: 'spawn-config.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/spawn-configs/:id',
      handler: 'spawn-config.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/spawn-configs/:id',
      handler: 'spawn-config.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
