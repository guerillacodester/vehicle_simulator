export default {
  routes: [
    {
      method: 'GET',
      path: '/stops',
      handler: 'stop.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/stops/:id',
      handler: 'stop.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/stops',
      handler: 'stop.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/stops/:id',
      handler: 'stop.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/stops/:id',
      handler: 'stop.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};