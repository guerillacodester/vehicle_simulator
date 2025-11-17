export default {
  routes: [
    {
      method: 'GET',
      path: '/route-geometry/:routeName',
      handler: 'route-geometry.getGeometry',
      config: {
        auth: false,
        policies: ['global::check-access-tier'],
      },
    },
  ],
};
