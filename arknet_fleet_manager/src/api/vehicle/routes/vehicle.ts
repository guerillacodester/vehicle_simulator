/**
 * vehicle router
 */

import { factories } from '@strapi/strapi';

export default factories.createCoreRouter('api::vehicle.vehicle', {
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