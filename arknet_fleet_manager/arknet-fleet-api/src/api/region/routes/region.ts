export default {
  routes: [
    {
      method: 'GET',
      path: '/regions',
      handler: 'region.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/regions/:id',
      handler: 'region.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/regions',
      handler: 'region.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/regions/:id',
      handler: 'region.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/regions/:id',
      handler: 'region.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
