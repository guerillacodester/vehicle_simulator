import { factories } from '@strapi/strapi'

export default factories.createCoreRouter('api::agency.agency' as any, {
  config: {
    find: {
      auth: false,
      policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'agency', operation: 'read' } }],
      middlewares: [],
    },
    findOne: {
      policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'agency', operation: 'read' } }],
      middlewares: [],
    },
    create: {
      policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'agency', operation: 'create' } }],
      middlewares: [],
    },
    update: {
      policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'agency', operation: 'update' } }],
      middlewares: [],
    },
    delete: {
      policies: [{ name: 'global::rbac-tier-policy', config: { contentType: 'agency', operation: 'delete' } }],
      middlewares: [],
    },
  },
});
