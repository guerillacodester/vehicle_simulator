export default {
  routes: [
    {
      method: 'GET',
      path: '/region-shapes',
      handler: 'region-shape.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/region-shapes/:id',
      handler: 'region-shape.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/region-shapes',
      handler: 'region-shape.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/region-shapes/:id',
      handler: 'region-shape.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/region-shapes/:id',
      handler: 'region-shape.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
