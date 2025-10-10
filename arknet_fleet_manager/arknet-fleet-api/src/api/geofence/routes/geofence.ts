export default {
  routes: [
    {
      method: 'GET',
      path: '/geofences',
      handler: 'geofence.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/geofences/:id',
      handler: 'geofence.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/geofences',
      handler: 'geofence.create',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/geofences/:id',
      handler: 'geofence.update',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/geofences/:id',
      handler: 'geofence.delete',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
