export default {
  routes: [
    {
      method: 'GET',
      path: '/drivers',
      handler: 'driver.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/drivers/:id',
      handler: 'driver.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/drivers',
      handler: 'driver.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/drivers/:id',
      handler: 'driver.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/drivers/:id',
      handler: 'driver.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};