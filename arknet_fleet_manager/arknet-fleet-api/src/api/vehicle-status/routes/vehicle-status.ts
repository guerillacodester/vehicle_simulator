export default {
  routes: [
    {
      method: 'GET',
      path: '/vehicle-statuses',
      handler: 'vehicle-status.find',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/vehicle-statuses/:id',
      handler: 'vehicle-status.findOne',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'POST',
      path: '/vehicle-statuses',
      handler: 'vehicle-status.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/vehicle-statuses/:id',
      handler: 'vehicle-status.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/vehicle-statuses/:id',
      handler: 'vehicle-status.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};