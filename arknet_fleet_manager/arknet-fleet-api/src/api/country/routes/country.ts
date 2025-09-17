export default {
  routes: [
    {
      method: 'GET',
      path: '/countries',
      handler: 'country.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/countries/:id',
      handler: 'country.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/countries',
      handler: 'country.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/countries/:id',
      handler: 'country.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/countries/:id',
      handler: 'country.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};