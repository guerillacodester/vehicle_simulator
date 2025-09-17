// import type { Core } from '@strapi/strapi';

export default {
  /**
   * An asynchronous register function that runs before
   * your application is initialized.
   *
   * This gives you an opportunity to extend code.
   */
  register({ strapi }) {
    // Add custom routes for simulator compatibility
    strapi.server.routes([
      {
        method: 'GET',
        path: '/health',
        handler: async (ctx) => {
          ctx.body = { status: 'ok', timestamp: new Date().toISOString() };
        },
        config: {
          auth: false,
        },
      },
      {
        method: 'GET', 
        path: '/api/v1/search/vehicle-driver-pairs',
        handler: async (ctx) => {
          // Mock data with correct format for simulator compatibility
          const mockAssignments = [
            {
              driver_employment_status: "active",
              registration: "TEST-001",
              route_code: "r1",
              driver_license: "DL123456",
              driver_name: "Test Driver",
              route_name: "Test Route 1",
              assignment_date: "2025-09-17T18:00:00Z"
            }
          ];
          ctx.body = mockAssignments;
        },
        config: {
          auth: false,
        },
      },
      {
        method: 'GET',
        path: '/api/v1/routes/public/:routeCode/geometry',
        handler: async (ctx) => {
          // Mock geometry data
          const mockGeometry = {
            route_id: ctx.params.routeCode,
            route_name: `Route ${ctx.params.routeCode}`,
            geometry: {
              type: "LineString",
              coordinates: [
                [-59.6463, 13.2810],
                [-59.6464, 13.2811], 
                [-59.6465, 13.2812]
              ]
            },
            coordinate_count: 3
          };
          ctx.body = mockGeometry;
        },
        config: {
          auth: false,
        },
      }
    ]);
  },

  /**
   * An asynchronous bootstrap function that runs before
   * your application gets started.
   *
   * This gives you an opportunity to set up your data model,
   * run jobs, or perform some special logic.
   */
  bootstrap({ strapi }) {
    // Set up public permissions for APIs on startup
    setTimeout(async () => {
      try {
        const publicRole = await strapi.entityService.findMany('plugin::users-permissions.role', {
          filters: { type: 'public' },
        });

        if (publicRole && publicRole.length > 0) {
          const roleId = publicRole[0].id;
          
          // Grant permissions for all our APIs
          const apiNames = ['vehicle', 'driver', 'route', 'trip', 'gps-device', 'vehicle-assignment'];
          const actions = ['find', 'findOne', 'create', 'update', 'delete'];
          
          for (const apiName of apiNames) {
            for (const action of actions) {
              try {
                await strapi.entityService.create('plugin::users-permissions.permission', {
                  data: {
                    action: `api::${apiName}.${apiName}.${action}`,
                    role: roleId,
                    enabled: true,
                  },
                });
              } catch (error) {
                // Permission might already exist, ignore
              }
            }
          }
          console.log('✅ Public API permissions configured');
        }
      } catch (error) {
        console.log('⚠️ Permission setup error:', error.message);
      }
    }, 2000);
  },
};
