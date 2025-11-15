export default {
  routes: [
    {
      method: 'GET',
      path: '/routes',
      handler: 'route.find',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/routes/:id',
      handler: 'route.findOne',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/routes',
      handler: 'route.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/routes/:id',
      handler: 'route.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/routes/:id',
      handler: 'route.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/routes/:routeName/geometry',
      handler: 'route.getGeometry',
      config: {
        auth: { scope: ['admin'] },
        policies: ['global::check-access-tier'],
        middlewares: [],
      },
    },
  ],
};