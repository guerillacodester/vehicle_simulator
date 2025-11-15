export default {
  routes: [
    {
      method: 'GET',
      path: '/vehicles',
      handler: 'vehicle.find',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/vehicles/:id',
      handler: 'vehicle.findOne',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'POST',
      path: '/vehicles',
      handler: 'vehicle.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/vehicles/:id',
      handler: 'vehicle.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/vehicles/:id',
      handler: 'vehicle.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};