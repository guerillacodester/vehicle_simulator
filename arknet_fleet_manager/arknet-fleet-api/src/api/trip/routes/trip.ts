export default {
  routes: [
    {
      method: 'GET',
      path: '/trips',
      handler: 'trip.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/trips/:id',
      handler: 'trip.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/trips',
      handler: 'trip.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/trips/:id',
      handler: 'trip.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/trips/:id',
      handler: 'trip.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};