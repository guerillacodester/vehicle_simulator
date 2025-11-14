/**
 * Socket.IO Configuration for ArkNet Transit System
 * 
 * This configuration enables real-time communication between:
 * - Commuter Service (spawns commuters in depot/route reservoirs)
 * - Vehicle Conductor (queries reservoirs, coordinates boarding)
 * - Depot Queue Manager (manages vehicle queues and departures)
 * 
 * Architecture:
 * - Strapi acts as Socket.IO hub on port 1337
 * - Event-driven pub/sub pattern for loose coupling
 * - Separate namespaces for depot and route reservoirs
 */

export default ({ env }: any) => ({
  enabled: true,
  
  // Socket.IO server options
  socketio: {
    // CORS configuration for cross-origin connections
    cors: {
      origin: env('SOCKETIO_CORS_ORIGIN', '*'),
      methods: ['GET', 'POST'],
      credentials: true,
    },
    
    // Connection settings
    pingTimeout: 60000, // 60 seconds
    pingInterval: 25000, // 25 seconds
    
    // Max HTTP buffer size for large payloads (route geometry, etc.)
    maxHttpBufferSize: 1e6, // 1 MB
    
    // Transport protocols (WebSocket preferred)
    transports: ['websocket', 'polling'],
    
    // Allow upgrades from polling to WebSocket
    allowUpgrades: true,
    
    // Cookie settings
    cookie: {
      name: 'arknet-socketio',
      httpOnly: true,
      sameSite: 'lax',
    },
  },
  
  // Namespaces configuration
  namespaces: {
    // Depot Reservoir: Outbound commuters only
    depot: '/depot-reservoir',
    
    // Route Reservoir: Bidirectional commuters (inbound/outbound)
    route: '/route-reservoir',
    
    // Vehicle Events: Real-time vehicle state updates
    vehicle: '/vehicle-events',
    
    // System Events: Health checks, monitoring
    system: '/system-events',
  },
  
  // Event logging for debugging
  logging: {
    enabled: env.bool('SOCKETIO_LOGGING', true),
    level: env('SOCKETIO_LOG_LEVEL', 'info'), // debug, info, warn, error
  },
});
