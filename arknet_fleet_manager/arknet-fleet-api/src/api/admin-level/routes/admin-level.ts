/**
 * admin-level router
 */

import { factories } from '@strapi/strapi';

export default {
  routes: [
    {
      method: 'GET',
      path: '/admin-levels',
      handler: 'admin-level.find',
      config: {
        policies: [],
        middlewares: [],
      },
    },
    {
      method: 'GET',
      path: '/admin-levels/:id',
      handler: 'admin-level.findOne',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
