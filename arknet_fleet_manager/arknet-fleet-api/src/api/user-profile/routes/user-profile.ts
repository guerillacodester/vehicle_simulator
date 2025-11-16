export default {
  routes: [
    {
      method: 'GET',
      path: '/user-profiles',
      handler: 'user-profile.find',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/user-profiles/:id',
      handler: 'user-profile.findOne',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'admin' } }],
        middlewares: [],
      },
    },
    {
      method: 'POST',
      path: '/user-profiles',
      handler: 'user-profile.create',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'superadmin' } }],
        middlewares: [],
      },
    },
    {
      method: 'PUT',
      path: '/user-profiles/:id',
      handler: 'user-profile.update',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'superadmin' } }],
        middlewares: [],
      },
    },
    {
      method: 'DELETE',
      path: '/user-profiles/:id',
      handler: 'user-profile.delete',
      config: {
        policies: [{ name: 'global::check-access-tier', config: { minTier: 'superadmin' } }],
        middlewares: [],
      },
    },
  ],
};
