import { factories } from '@strapi/strapi';
export default {
  routes: [
    {
      method: 'GET',
      path: '/geofence-geometries',
      handler: 'geofence-geometry.find',
      config: { policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }], middlewares: [] },
    },
    {
      method: 'GET',
      path: '/geofence-geometries/:id',
      handler: 'geofence-geometry.findOne',
      config: { policies: [{ name: 'global::check-access-tier', config: { minTier: 'guest' } }], middlewares: [] },
    },
    {
      method: 'POST',
      path: '/geofence-geometries',
      handler: 'geofence-geometry.create',
      config: { policies: [{ name: 'global::check-access-tier', config: {} }], middlewares: [], auth: { scope: ['admin'] } },
    },
    {
      method: 'PUT',
      path: '/geofence-geometries/:id',
      handler: 'geofence-geometry.update',
      config: { policies: [{ name: 'global::check-access-tier', config: {} }], middlewares: [], auth: { scope: ['admin'] } },
    },
    {
      method: 'DELETE',
      path: '/geofence-geometries/:id',
      handler: 'geofence-geometry.delete',
      config: { policies: [{ name: 'global::check-access-tier', config: {} }], middlewares: [], auth: { scope: ['admin'] } },
    },
  ],
};
// Converting to manual routes with AccessTier policy
