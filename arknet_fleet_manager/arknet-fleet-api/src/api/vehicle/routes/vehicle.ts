export default {
  routes: [
    {
      method: 'GET',
      path: '/vehicles',
      handler: 'vehicle.find',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'vehicle', operation: 'read' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'GET',
      path: '/vehicles/:id',
      handler: 'vehicle.findOne',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'vehicle', operation: 'read' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'POST',
      path: '/vehicles',
      handler: 'vehicle.create',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'vehicle', operation: 'create' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'PUT',
      path: '/vehicles/:id',
      handler: 'vehicle.update',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'vehicle', operation: 'update' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
    {
      method: 'DELETE',
      path: '/vehicles/:id',
      handler: 'vehicle.delete',
      config: {
        policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'vehicle', operation: 'delete' } }],
        middlewares: [],
        auth: { scope: ['admin'] },
      },
    },
  ],
};
