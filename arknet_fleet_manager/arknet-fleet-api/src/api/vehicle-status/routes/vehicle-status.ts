export default {
  routes: [
    {
      method: 'GET',
      path: '/vehicle-statuses',
      handler: 'vehicle-status.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/vehicle-statuses/:id',
      handler: 'vehicle-status.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/vehicle-statuses',
      handler: 'vehicle-status.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/vehicle-statuses/:id',
      handler: 'vehicle-status.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/vehicle-statuses/:id',
      handler: 'vehicle-status.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};