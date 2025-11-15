export default {
  routes: [
    {
      method: 'GET',
      path: '/landuse-zones',
      handler: 'landuse-zone.find',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/landuse-zones/:id',
      handler: 'landuse-zone.findOne',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'POST',
      path: '/landuse-zones',
      handler: 'landuse-zone.create',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/landuse-zones/:id',
      handler: 'landuse-zone.update',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/landuse-zones/:id',
      handler: 'landuse-zone.delete',
      config: {
        policies: ['global::check-access-tier'],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};
