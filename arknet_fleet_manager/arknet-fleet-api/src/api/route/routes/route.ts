export default {
  routes: [
    {
      method: 'GET',
      path: '/routes',
      handler: 'route.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/routes/:id',
      handler: 'route.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/routes',
      handler: 'route.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/routes/:id',
      handler: 'route.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/routes/:id',
      handler: 'route.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/routes/test-geometry/:routeName',
      handler: 'route.testGeometry',
      config: {
        auth: false,
        policies: [],
        middlewares: [],
      },
    },
  ],
};