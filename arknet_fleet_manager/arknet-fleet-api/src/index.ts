import type { Core } from '@strapi/strapi';
import { initializeSocketIO, shutdownSocketIO } from './socketio/server';

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
  bootstrap({ strapi }: { strapi: Core.Strapi }) {
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
