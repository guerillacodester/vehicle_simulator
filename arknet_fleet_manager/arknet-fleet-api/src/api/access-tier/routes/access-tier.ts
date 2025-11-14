export default {
  routes: [
    {
      method: 'GET',
      path: '/access-tiers',
      handler: 'access-tier.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/access-tiers/:id',
      handler: 'access-tier.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/access-tiers',
      handler: 'access-tier.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/access-tiers/:id',
      handler: 'access-tier.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/access-tiers/:id',
      handler: 'access-tier.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
