export default {
  routes: [
    {
      method: 'GET',
      path: '/geometry-points',
      handler: 'geometry-point.find',
    },
    {
      method: 'GET',
      path: '/geometry-points/:id',
      handler: 'geometry-point.findOne',
    },
    {
      method: 'POST',
      path: '/geometry-points',
      handler: 'geometry-point.create',
    },
    {
      method: 'PUT',
      path: '/geometry-points/:id',
      handler: 'geometry-point.update',
    },
    {
      method: 'DELETE',
      path: '/geometry-points/:id',
      handler: 'geometry-point.delete',
    },
  ],
};
