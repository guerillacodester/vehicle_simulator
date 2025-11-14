"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const server_1 = require("./socketio/server");
/**
 * Set public and authenticated permissions for APIs that need to be accessible
 * from the admin panel and public endpoints.
 */
async function setPublicPermissions(strapi) {
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
                const existingPermission = existingPermissions.find((p) => p.action === permissionName);
                if (existingPermission && !existingPermission.enabled) {
                    await strapi.db.query('plugin::users-permissions.permission').update({
                        where: { id: existingPermission.id },
                        data: { enabled: true },
                    });
                    console.log(`[Bootstrap] ✅ Enabled ${role} permission: ${action} on ${contentType}`);
                }
                else if (!existingPermission) {
                    // Create new permission if it doesn't exist
                    await strapi.db.query('plugin::users-permissions.permission').create({
                        data: {
                            action: permissionName,
                            role: roleEntity.id,
                            enabled: true,
                        },
                    });
                    console.log(`[Bootstrap] ✅ Created ${role} permission: ${action} on ${contentType}`);
                }
                else {
                    console.log(`[Bootstrap] ✓ Permission already enabled: ${role}.${action} on ${contentType}`);
                }
            }
        }
        catch (error) {
            console.error(`[Bootstrap] ❌ Failed to set permissions for ${role} on ${contentType}:`, error);
        }
    }
}
exports.default = {
    /**
     * An asynchronous register function that runs before
     * your application is initialized.
     *
     * This gives you an opportunity to extend code.
     */
    register({ strapi }) {
        // Register GraphQL extensions from modular folder structure
        const path = require('path');
        const fs = require('fs');
        // Resolve path - check if running from dist or src
        const resolverPath = path.join(__dirname, '../../src/extensions/graphql/routeGeometry/resolvers/routeGeometry.js');
        const routeGeometryResolver = require(resolverPath);
        const extensionService = strapi.plugin('graphql').service('extension');
        extensionService.use(({ nexus }) => ({
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
    async bootstrap({ strapi }) {
        var _a, _b, _c, _d, _e;
        // Configure API permissions for authenticated and public access
        console.log('[Bootstrap] Configuring API permissions...');
        await setPublicPermissions(strapi);
        // Configure GeoJSON file upload support
        console.log('[Bootstrap] Configuring GeoJSON file support...');
        const uploadPlugin = strapi.plugin('upload');
        if (uploadPlugin) {
            const originalIsValidFileType = (_a = uploadPlugin.service('upload')) === null || _a === void 0 ? void 0 : _a.isValidFileType;
            if (originalIsValidFileType) {
                uploadPlugin.service('upload').isValidFileType = (file) => {
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
            redis.get('strapi_test_key').then((result) => {
                console.log(`[Redis Test] GET strapi_test_key:`, result); // Should log 'hello_redis'
            }).catch((err) => {
                console.error('[Redis Test] Error getting key:', err);
            });
        }).catch((err) => {
            console.error('[Redis Test] Error setting key:', err);
        });
        // Initialize Socket.IO server for real-time commuter-vehicle coordination
        console.log('[Bootstrap] Initializing Socket.IO server...');
        const io = (0, server_1.initializeSocketIO)(strapi);
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
            (0, server_1.shutdownSocketIO)(strapi);
        };
        process.on('SIGTERM', gracefulShutdown);
        process.on('SIGINT', gracefulShutdown);
        // Backfill cached labels on route-depot associations so admin UI shows readable names
        try {
            console.log('[Bootstrap] Backfilling route-depot cached labels (route_short_name, depot_name, display_name)...');
            const missing = await strapi.entityService.findMany('api::route-depot.route-depot', {
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
                for (const rec of missing) {
                    const data = {};
                    const routeShort = (_b = rec === null || rec === void 0 ? void 0 : rec.route_short_name) !== null && _b !== void 0 ? _b : (_c = rec === null || rec === void 0 ? void 0 : rec.route) === null || _c === void 0 ? void 0 : _c.short_name;
                    const depotName = (_d = rec === null || rec === void 0 ? void 0 : rec.depot_name) !== null && _d !== void 0 ? _d : (_e = rec === null || rec === void 0 ? void 0 : rec.depot) === null || _e === void 0 ? void 0 : _e.name;
                    if (!(rec === null || rec === void 0 ? void 0 : rec.route_short_name) && routeShort)
                        data.route_short_name = routeShort;
                    if (!(rec === null || rec === void 0 ? void 0 : rec.depot_name) && depotName)
                        data.depot_name = depotName;
                    if (!(rec === null || rec === void 0 ? void 0 : rec.display_name) && depotName && (rec === null || rec === void 0 ? void 0 : rec.distance_from_route_m) !== undefined) {
                        const rounded = Math.round(rec.distance_from_route_m);
                        data.display_name = `${depotName} - ${rounded}m`;
                    }
                    if (Object.keys(data).length > 0) {
                        await strapi.entityService.update('api::route-depot.route-depot', rec.id, { data });
                        updated += 1;
                    }
                }
                console.log(`[Bootstrap] ✓ Backfilled ${updated} route-depot records`);
            }
            else {
                console.log('[Bootstrap] ✓ No route-depot records needed backfilling');
            }
        }
        catch (err) {
            console.error('[Bootstrap] ⚠️ Failed to backfill route-depot cached labels:', err);
        }
    },
};
//# sourceMappingURL=index.js.map