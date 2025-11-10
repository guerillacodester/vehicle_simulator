import type { Core } from '@strapi/strapi';
import { initializeSocketIO, shutdownSocketIO } from './socketio/server';

/**
 * Set public and authenticated permissions for APIs that need to be accessible
 * from the admin panel and public endpoints.
 */
async function setPublicPermissions(strapi: Core.Strapi) {
  const permissionsToEnable = [
    {
      role: 'authenticated',
      contentType: 'api::admin-level.admin-level',
      actions: ['find', 'findOne'],
    },
    {
      role: 'public',
      contentType: 'api::admin-level.admin-level',
      actions: ['find', 'findOne'],
    },
  ];

  for (const { role, contentType, actions } of permissionsToEnable) {
    try {
      // Get the role
      const roleEntity = await strapi.db.query('plugin::users-permissions.role').findOne({
        where: { type: role },
      });

      if (!roleEntity) {
        console.warn(`[Bootstrap] Role '${role}' not found, skipping permissions for ${contentType}`);
        continue;
      }

      // Get existing permissions for this role and content type
      const existingPermissions = await strapi.db.query('plugin::users-permissions.permission').findMany({
        where: {
          role: roleEntity.id,
        },
      });

      // Enable specified actions
      for (const action of actions) {
        const permissionName = `api::admin-level.admin-level.${action}`;
        
        const existingPermission = existingPermissions.find(
          (p: any) => p.action === permissionName
        );

        if (existingPermission && !existingPermission.enabled) {
          await strapi.db.query('plugin::users-permissions.permission').update({
            where: { id: existingPermission.id },
            data: { enabled: true },
          });
          console.log(`[Bootstrap] ✅ Enabled ${role} permission: ${action} on ${contentType}`);
        } else if (!existingPermission) {
          // Create new permission if it doesn't exist
          await strapi.db.query('plugin::users-permissions.permission').create({
            data: {
              action: permissionName,
              role: roleEntity.id,
              enabled: true,
            },
          });
          console.log(`[Bootstrap] ✅ Created ${role} permission: ${action} on ${contentType}`);
        } else {
          console.log(`[Bootstrap] ✓ Permission already enabled: ${role}.${action} on ${contentType}`);
        }
      }
    } catch (error) {
      console.error(`[Bootstrap] ❌ Failed to set permissions for ${role} on ${contentType}:`, error);
    }
  }
}

export default {
  /**
   * An asynchronous register function that runs before
   * your application is initialized.
   *
   * This gives you an opportunity to extend code.
   */
  register({ strapi }: { strapi: Core.Strapi }) {
    // Register GraphQL custom query for route geometry
    const extensionService = strapi.plugin('graphql').service('extension');

    extensionService.use(({ nexus }: any) => ({
      resolversConfig: {
        'Query.routeGeometry': {
          auth: false,
          policies: [],
        },
      },
      resolvers: {
        Query: {
          routeGeometry: async (_root: any, args: any) => {
            const { routeName } = args;
            const result = await strapi
              .service('api::route.route')
              .fetchRouteGeometry(routeName);

            return {
              success: true,
              routeName,
              metrics: result.metrics,
              coordinateCount: result.coords.length,
              segmentCount: result.segments.length,
              coordinates: result.coords,
            };
          },
        },
      },
      types: [
        nexus.extendType({
          type: 'Query',
          definition(t: any) {
            t.field('routeGeometry', {
              type: 'RouteGeometryResponse',
              args: {
                routeName: nexus.nonNull(nexus.stringArg()),
              },
            });
          },
        }),
        
        nexus.objectType({
          name: 'RouteGeometryResponse',
          definition(t: any) {
            t.nonNull.boolean('success');
            t.nonNull.string('routeName');
            t.field('metrics', { type: 'RouteMetrics' });
            t.nonNull.int('coordinateCount');
            t.nonNull.int('segmentCount');
            t.list.field('coordinates', {
              type: 'JSON',
            });
          },
        }),
        
        nexus.objectType({
          name: 'RouteMetrics',
          definition(t: any) {
            t.nonNull.int('totalPoints');
            t.nonNull.float('estimatedLengthKm');
            t.nonNull.int('segments');
            t.nonNull.int('reversedCount');
          },
        }),
      ],
    }));
  },

  /**
   * An asynchronous bootstrap function that runs before
   * your application gets started.
   *
   * This gives you an opportunity to set up your data model,
   * run jobs, or perform some special logic.
   */
  async bootstrap({ strapi }: { strapi: Core.Strapi }) {
    // Configure API permissions for authenticated and public access
    console.log('[Bootstrap] Configuring API permissions...');
    await setPublicPermissions(strapi);
    
    // Configure GeoJSON file upload support
    console.log('[Bootstrap] Configuring GeoJSON file support...');
    const uploadPlugin = strapi.plugin('upload');
    
    if (uploadPlugin) {
      const originalIsValidFileType = uploadPlugin.service('upload')?.isValidFileType;
      
      if (originalIsValidFileType) {
        uploadPlugin.service('upload').isValidFileType = (file: any) => {
          // Allow .geojson files
          if (file.name && file.name.toLowerCase().endsWith('.geojson')) {
            console.log(`[Upload] Accepting GeoJSON file: ${file.name}`);
            return true;
          }
          
          // Fall back to original validation
          return originalIsValidFileType(file);
        };
        
        console.log('[Bootstrap] ✅ GeoJSON file uploads enabled');
      }
    }
    
      // Redis client initialization
      const Redis = require('ioredis');
      const redis = new Redis();
    
      // Simple Redis connectivity test
      redis.set('strapi_test_key', 'hello_redis').then(() => {
        redis.get('strapi_test_key').then((result: string | null) => {
          console.log(`[Redis Test] GET strapi_test_key:`, result); // Should log 'hello_redis'
        }).catch((err: Error) => {
          console.error('[Redis Test] Error getting key:', err);
        });
      }).catch((err: Error) => {
        console.error('[Redis Test] Error setting key:', err);
      });
    
    // Initialize Socket.IO server for real-time commuter-vehicle coordination
    console.log('[Bootstrap] Initializing Socket.IO server...');
    const io = initializeSocketIO(strapi);
    
    // Store io instance on strapi for use in controllers
    // @ts-ignore - Extending Strapi type
    strapi.io = io;
    
    console.log('[Bootstrap] Socket.IO server initialized successfully');
    console.log('[Bootstrap] Available namespaces:');
    console.log('  - /depot-reservoir (Outbound commuters)');
    console.log('  - /route-reservoir (Inbound/Outbound commuters)');
    console.log('  - /vehicle-events (Vehicle state updates)');
    console.log('  - /system-events (Health checks, monitoring)');
    
    // Handle graceful shutdown
    const gracefulShutdown = () => {
      console.log('[Bootstrap] Shutting down Socket.IO server...');
      shutdownSocketIO(strapi);
    };
    
    process.on('SIGTERM', gracefulShutdown);
    process.on('SIGINT', gracefulShutdown);

    // Backfill cached labels on route-depot associations so admin UI shows readable names
    try {
      console.log('[Bootstrap] Backfilling route-depot cached labels (route_short_name, depot_name, display_name)...');
      const missing = await strapi.entityService.findMany('api::route-depot.route-depot' as any, {
        filters: {
          $or: [
            { route_short_name: { $null: true } },
            { depot_name: { $null: true } },
            { display_name: { $null: true } }
          ],
        },
        populate: {
          route: { fields: ['short_name'] },
          depot: { fields: ['name'] },
        },
        limit: 1000,
      });

      if (Array.isArray(missing) && missing.length > 0) {
        let updated = 0;
        for (const rec of missing as any[]) {
          const data: any = {};
          const routeShort = rec?.route_short_name ?? rec?.route?.short_name;
          const depotName = rec?.depot_name ?? rec?.depot?.name;
          if (!rec?.route_short_name && routeShort) data.route_short_name = routeShort;
          if (!rec?.depot_name && depotName) data.depot_name = depotName;
          if (!rec?.display_name && depotName && rec?.distance_from_route_m !== undefined) {
            const rounded = Math.round(rec.distance_from_route_m);
            data.display_name = `${depotName} - ${rounded}m`;
          }
          if (Object.keys(data).length > 0) {
            await strapi.entityService.update('api::route-depot.route-depot' as any, rec.id, { data });
            updated += 1;
          }
        }
        console.log(`[Bootstrap] ✓ Backfilled ${updated} route-depot records`);
      } else {
        console.log('[Bootstrap] ✓ No route-depot records needed backfilling');
      }
    } catch (err) {
      console.error('[Bootstrap] ⚠️ Failed to backfill route-depot cached labels:', err);
    }
  },
};
