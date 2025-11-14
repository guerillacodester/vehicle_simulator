export default {
  routes: [
    {
      method: 'GET',
      path: '/shapes',
      handler: 'shape.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/shapes/:id',
      handler: 'shape.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/shapes',
      handler: 'shape.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/shapes/:id',
      handler: 'shape.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/shapes/:id',
      handler: 'shape.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};