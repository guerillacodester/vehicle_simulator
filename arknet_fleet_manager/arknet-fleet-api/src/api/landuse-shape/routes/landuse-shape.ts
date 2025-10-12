export default {
  routes: [
    {
      method: 'GET',
      path: '/landuse-shapes',
      handler: 'landuse-shape.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/landuse-shapes/:id',
      handler: 'landuse-shape.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/landuse-shapes',
      handler: 'landuse-shape.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/landuse-shapes/:id',
      handler: 'landuse-shape.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/landuse-shapes/:id',
      handler: 'landuse-shape.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
