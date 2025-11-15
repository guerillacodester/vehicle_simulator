import type { Core } from '@strapi/strapi';
import { initializeSocketIO, shutdownSocketIO } from './socketio/server';

/**
 * Set public and authenticated permissions for APIs that need to be accessible
 * from the admin panel and public endpoints.
 */
async function setPublicPermissions(strapi: Core.Strapi) {
  // New behavior: scan route files to determine per-action minTier requirements
  // and enable/disable Users & Permissions checkboxes for public/authenticated roles
  const path = require('path');
  const fs = require('fs');
  const apiRoot = path.join(__dirname, './api');

  const adminOnly = new Set([
    'access-tier',
    'geojson-import',
    'import-geojson',
    'user-profile',
  ]);

  // Actions of interest (commonly exposed by factories.createCoreRouter)
  const actions = ['find', 'findOne', 'create', 'update', 'delete'];

  // Helper: normalize tier string to TitleCase used by policy
  const toTitle = (s: string) => {
    if (!s) return s;
    return s.charAt(0).toUpperCase() + s.slice(1).toLowerCase();
  };

  // Read all API directories
  let apiList: string[] = [];
  try {
    apiList = fs.readdirSync(apiRoot).filter((name: string) => {
      try { return fs.statSync(path.join(apiRoot, name)).isDirectory() && name[0] !== '.'; } catch (e) { return false; }
    });
  } catch (err) {
    console.warn('[Bootstrap] Could not read api directory for permissions sync:', err);
  }

  // Map contentType -> action -> minTier (string TitleCase)
  const ctActionTier: Record<string, Record<string, string | null>> = {};

  for (const apiName of apiList) {
    const contentType = `api::${apiName}.${apiName}`;
    ctActionTier[contentType] = {};
    // default to null (no explicit tier)
    for (const a of actions) ctActionTier[contentType][a] = null;

    if (adminOnly.has(apiName)) continue;

    // Read any routes files in the api folder
    const routesDir = path.join(apiRoot, apiName, 'routes');
    try {
      const files = fs.existsSync(routesDir) ? fs.readdirSync(routesDir).filter((f: string) => f.endsWith('.ts') || f.endsWith('.js')) : [];
      for (const file of files) {
        const filePath = path.join(routesDir, file);
        let content = '';
        try { content = fs.readFileSync(filePath, 'utf8'); } catch (e) { continue; }

        // For each action, look for patterns like "find: { ... policies: [{ name: 'global::check-access-tier', config: { minTier: 'Viewer' } }] }"
        for (const action of actions) {
          const actionRegex = new RegExp(`${action}\s*:\s*\{[\s\S]{0,800}?name\s*:\s*['\"]global::check-access-tier['\"][\s\S]{0,200}?minTier\s*:\s*['\"]([^'\"]+)['\"]`, 'i');
          const m = content.match(actionRegex);
          if (m && m[1]) {
            ctActionTier[contentType][action] = toTitle(m[1]);
            continue;
          }

          // Fallback: route-object style where each route has a handler and config; try to find "handler.*.action" near a policies block
          const routeRegex = new RegExp(`handler\s*:\s*['\"][^'\"]*\\.(?:${action})['\"][\s\S]{0,200}?policies\s*:\s*\[([\s\S]{0,500})\]`, 'i');
          const rm = content.match(routeRegex);
          if (rm && rm[1]) {
            const polBlock = rm[1];
            const minMatch = polBlock.match(/minTier\s*:\s*['\"]([^'\"]+)['\"]/i);
            if (minMatch && minMatch[1]) ctActionTier[contentType][action] = toTitle(minMatch[1]);
          }
        }
      }
    } catch (err) {
      // ignore individual api read failures
    }
  }

  // Determine desired enabled state for public/authenticated based on tiers
  // Tier hierarchy (matching policy implementation)
  const tierHierarchy = ['Guest','Viewer','Operator','Dispatcher','Manager','Admin','SuperAdmin'];

  // Helper to check if tier a <= tier b
  const tierIndex = (t: string | null) => (t ? tierHierarchy.indexOf(t) : -1);

  // Roles
  const authRole = await strapi.db.query('plugin::users-permissions.role').findOne({ where: { type: 'authenticated' } });
  const publicRole = await strapi.db.query('plugin::users-permissions.role').findOne({ where: { type: 'public' } });

  // Fetch existing permissions for both roles to minimize DB ops
  const existingAuth = authRole ? await strapi.db.query('plugin::users-permissions.permission').findMany({ where: { role: authRole.id } }) : [];
  const existingPublic = publicRole ? await strapi.db.query('plugin::users-permissions.permission').findMany({ where: { role: publicRole.id } }) : [];

  // Walk each contentType/action and set enabled state
  for (const [contentType, actionMap] of Object.entries(ctActionTier)) {
    for (const action of Object.keys(actionMap)) {
      const minTier = actionMap[action] || null;
      // Default desired: if no explicit minTier, preserve existing behavior (enable find/findOne for authenticated)
      let desiredAuth = null; // null means preserve
      let desiredPublic = null;

      if (minTier) {
        const idx = tierIndex(minTier);
        if (idx === -1) {
          // unknown tier, skip
          desiredAuth = false;
          desiredPublic = false;
        } else {
          // If minTier is Guest -> public + authenticated should be enabled
          if (minTier === 'Guest') {
            desiredPublic = true; desiredAuth = true;
          } else if (idx <= tierHierarchy.indexOf('Viewer')) {
            // Viewer or below -> authenticated allowed
            desiredAuth = true; desiredPublic = false;
          } else {
            // Operator and above -> do not enable default authenticated/public
            desiredAuth = false; desiredPublic = false;
          }
        }
      } else {
        // no minTier provided: preserve previous behavior only for find/findOne
        if (action === 'find' || action === 'findOne') {
          desiredAuth = true; desiredPublic = null; // leave public unchanged
        }
      }

      const actionName = `${contentType}.${action}`;

      // Apply for authenticated
      if (authRole && desiredAuth !== null) {
        const existing = existingAuth.find((p: any) => p.action === actionName);
        if (existing) {
          if (existing.enabled !== desiredAuth) {
            await strapi.db.query('plugin::users-permissions.permission').update({ where: { id: existing.id }, data: { enabled: desiredAuth } });
            console.log(`[Bootstrap] ${desiredAuth ? '✅ Enabled' : '🔒 Disabled'} authenticated permission: ${action} on ${contentType}`);
          }
        } else if (desiredAuth) {
          await strapi.db.query('plugin::users-permissions.permission').create({ data: { action: actionName, role: authRole.id, enabled: true } });
          console.log(`[Bootstrap] ✅ Created authenticated permission: ${action} on ${contentType}`);
        }
      }

      // Apply for public
      if (publicRole && desiredPublic !== null) {
        const existing = existingPublic.find((p: any) => p.action === actionName);
        if (existing) {
          if (existing.enabled !== desiredPublic) {
            await strapi.db.query('plugin::users-permissions.permission').update({ where: { id: existing.id }, data: { enabled: desiredPublic } });
            console.log(`[Bootstrap] ${desiredPublic ? '✅ Enabled' : '🔒 Disabled'} public permission: ${action} on ${contentType}`);
          }
        } else if (desiredPublic) {
          await strapi.db.query('plugin::users-permissions.permission').create({ data: { action: actionName, role: publicRole.id, enabled: true } });
          console.log(`[Bootstrap] ✅ Created public permission: ${action} on ${contentType}`);
        }
      }
    }
  }

  // Preserve explicit admin-level behavior for public role as before
  try {
    if (publicRole) {
      const contentType = 'api::admin-level.admin-level';
      for (const action of ['find', 'findOne']) {
        const actionName = `${contentType}.${action}`;
        const existing = await strapi.db.query('plugin::users-permissions.permission').findOne({ where: { role: publicRole.id, action: actionName } });
        if (existing && !existing.enabled) {
          await strapi.db.query('plugin::users-permissions.permission').update({ where: { id: existing.id }, data: { enabled: true } });
          console.log(`[Bootstrap] ✅ Enabled public permission: ${action} on ${contentType}`);
        } else if (!existing) {
          await strapi.db.query('plugin::users-permissions.permission').create({ data: { action: actionName, role: publicRole.id, enabled: true } });
          console.log(`[Bootstrap] ✅ Created public permission: ${action} on ${contentType}`);
        }
      }
    }
  } catch (err) {
    console.error('[Bootstrap] ❌ Failed to preserve admin-level public permissions:', err);
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
    // Register GraphQL extensions from modular folder structure
    const path = require('path');
    const fs = require('fs');
    
    // Resolve path - check if running from dist or src
    const resolverPath = path.join(__dirname, '../../src/extensions/graphql/routeGeometry/resolvers/routeGeometry.js');
    const routeGeometryResolver = require(resolverPath);
    const extensionService = strapi.plugin('graphql').service('extension');

    extensionService.use(({ nexus }: any) => ({
      resolversConfig: {
        'Query.routeGeometry': {
          auth: false,
          policies: [],
        },
      },
      types: [
        ...routeGeometryResolver({ nexus, strapi }),
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
