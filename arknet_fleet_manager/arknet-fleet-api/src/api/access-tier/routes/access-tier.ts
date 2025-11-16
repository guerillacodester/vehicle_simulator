export default {
  routes: [
    {
      method: 'GET',
      path: '/access-tiers',
      handler: 'access-tier.find',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'access_tier', operation: 'read' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/access-tiers/:id',
      handler: 'access-tier.findOne',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'access_tier', operation: 'read' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'POST',
      path: '/access-tiers',
      handler: 'access-tier.create',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'access_tier', operation: 'create' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/access-tiers/:id',
      handler: 'access-tier.update',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'access_tier', operation: 'update' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/access-tiers/:id',
      handler: 'access-tier.delete',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'access_tier', operation: 'delete' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};

