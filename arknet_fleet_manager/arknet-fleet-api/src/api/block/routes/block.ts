export default {
  routes: [
    {
      method: 'GET',
      path: '/blocks',
      handler: 'block.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/blocks/:id',
      handler: 'block.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/blocks',
      handler: 'block.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/blocks/:id',
      handler: 'block.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/blocks/:id',
      handler: 'block.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};