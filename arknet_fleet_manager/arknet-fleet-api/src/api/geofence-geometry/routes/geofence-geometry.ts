export default {
  routes: [
    {
      method: 'GET',
      path: '/geofence-geometries',
      handler: 'geofence-geometry.find',
    },
    {
      method: 'GET',
      path: '/geofence-geometries/:id',
      handler: 'geofence-geometry.findOne',
    },
    {
      method: 'POST',
      path: '/geofence-geometries',
      handler: 'geofence-geometry.create',
    },
    {
      method: 'PUT',
      path: '/geofence-geometries/:id',
      handler: 'geofence-geometry.update',
    },
    {
      method: 'DELETE',
      path: '/geofence-geometries/:id',
      handler: 'geofence-geometry.delete',
    },
  ],
};
