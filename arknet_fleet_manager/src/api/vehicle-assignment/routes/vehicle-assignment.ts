import { factories } from '@strapi/strapi';

export default factories.createCoreRouter('api::vehicle-assignment.vehicle-assignment', {
  config: {
    find: {
      middlewares: [],
    },
    findOne: {
      middlewares: [],
    },
    create: {
      middlewares: [],
    },
    update: {
      middlewares: [],
    },
    delete: {
      middlewares: [],
    },
  },
});

// Custom routes for legacy API compatibility
export const customRoutes = {
  routes: [
    {
      method: 'GET',
      path: '/api/v1/vehicle-assignments/active',
      handler: 'api::vehicle-assignment.vehicle-assignment.active',
      config: {
        auth: false,
      },
    },
  ],
};
