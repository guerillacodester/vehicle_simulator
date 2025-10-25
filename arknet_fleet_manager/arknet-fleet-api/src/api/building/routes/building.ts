export default {
  routes: [
    {
      method: 'GET',
      path: '/buildings',
      handler: 'building.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/buildings/:id',
      handler: 'building.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/buildings',
      handler: 'building.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/buildings/:id',
      handler: 'building.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/buildings/:id',
      handler: 'building.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
