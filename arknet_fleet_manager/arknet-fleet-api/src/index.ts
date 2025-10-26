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
  register(/* { strapi }: { strapi: Core.Strapi } */) {},

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
  },
};
