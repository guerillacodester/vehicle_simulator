/**
 * Socket.IO Server Bootstrap
 * 
 * Initializes the Socket.IO server within Strapi and sets up
 * event routing, connection management, and namespace handling.
 */

import { Server as SocketIOServer } from 'socket.io';
import type { Core } from '@strapi/strapi';
import { EventTypes, validateMessage } from './message-format';
import type { SocketIOMessage } from './message-format';

/**
 * Connection statistics
 */
interface ConnectionStats {
  totalConnections: number;
  activeConnections: number;
  messagesProcessed: number;
  lastMessageTime: Date | null;
  startTime: Date;
}

/**
 * Initialize Socket.IO server
 */
export function initializeSocketIO(strapi: Core.Strapi): SocketIOServer {
  const config = strapi.config.get('socket') as any;
  
  // Create Socket.IO server instance
  const io = new SocketIOServer(strapi.server.httpServer, config.socketio);
  
  // Connection statistics
  const stats: ConnectionStats = {
    totalConnections: 0,
    activeConnections: 0,
    messagesProcessed: 0,
    lastMessageTime: null,
    startTime: new Date(),
  };
  
  // Logging helper
  const log = (level: string, message: string, data?: any) => {
    if (config.logging.enabled) {
      const timestamp = new Date().toISOString();
      const logMessage = `[${timestamp}] [SocketIO] [${level.toUpperCase()}] ${message}`;
      
      if (data) {
        console.log(logMessage, data);
      } else {
        console.log(logMessage);
      }
    }
  };
  
  // Set up namespaces
  const depotNamespace = io.of(config.namespaces.depot);
  const routeNamespace = io.of(config.namespaces.route);
  const vehicleNamespace = io.of(config.namespaces.vehicle);
  const systemNamespace = io.of(config.namespaces.system);
  
  log('info', 'Socket.IO server initialized', {
    namespaces: Object.values(config.namespaces),
    cors: config.socketio.cors.origin,
  });
  
  /**
   * Connection handler for all namespaces
   */
  const handleConnection = (namespace: string) => (socket: any) => {
    stats.totalConnections++;
    stats.activeConnections++;
    
    log('info', `Client connected to ${namespace}`, {
      socketId: socket.id,
      activeConnections: stats.activeConnections,
    });
    
    // Notify system of connection
    systemNamespace.emit('message', {
      id: `conn_${Date.now()}`,
      type: EventTypes.SERVICE_CONNECTED,
      timestamp: new Date().toISOString(),
      source: 'socketio-server',
      data: {
        namespace,
        socketId: socket.id,
        activeConnections: stats.activeConnections,
      },
    });
    
    // Handle messages
    socket.on('message', (message: any) => {
      try {
        if (!validateMessage(message)) {
          log('warn', 'Invalid message format received', { message });
          socket.emit('error', {
            id: `err_${Date.now()}`,
            type: EventTypes.ERROR,
            timestamp: new Date().toISOString(),
            source: 'socketio-server',
            data: {
              error: 'Invalid message format',
              receivedMessage: message,
            },
          });
          return;
        }
        
        stats.messagesProcessed++;
        stats.lastMessageTime = new Date();
        
        log('debug', `Message received on ${namespace}`, {
          type: message.type,
          source: message.source,
          target: message.target,
        });
        
        // Route message based on target
        routeMessage(io, namespace, socket, message);
      } catch (error) {
        log('error', 'Error processing message', { error, message });
        socket.emit('error', {
          id: `err_${Date.now()}`,
          type: EventTypes.ERROR,
          timestamp: new Date().toISOString(),
          source: 'socketio-server',
          data: {
            error: String(error),
          },
        });
      }
    });
    
    // Handle disconnection
    socket.on('disconnect', (reason: string) => {
      stats.activeConnections--;
      
      log('info', `Client disconnected from ${namespace}`, {
        socketId: socket.id,
        reason,
        activeConnections: stats.activeConnections,
      });
      
      // Notify system of disconnection
      systemNamespace.emit('message', {
        id: `disc_${Date.now()}`,
        type: EventTypes.SERVICE_DISCONNECTED,
        timestamp: new Date().toISOString(),
        source: 'socketio-server',
        data: {
          namespace,
          socketId: socket.id,
          reason,
          activeConnections: stats.activeConnections,
        },
      });
    });
    
    // Handle errors
    socket.on('error', (error: Error) => {
      log('error', `Socket error on ${namespace}`, {
        socketId: socket.id,
        error: error.message,
      });
    });
  };
  
  // Attach connection handlers to namespaces
  depotNamespace.on('connection', handleConnection(config.namespaces.depot));
  routeNamespace.on('connection', handleConnection(config.namespaces.route));
  vehicleNamespace.on('connection', handleConnection(config.namespaces.vehicle));
  systemNamespace.on('connection', handleConnection(config.namespaces.system));
  
  /**
   * Route message to appropriate target(s)
   */
  function routeMessage(
    io: SocketIOServer,
    namespace: string,
    socket: any,
    message: SocketIOMessage
  ) {
    const ns = io.of(namespace);
    
    if (!message.target) {
      // Broadcast to all clients in namespace (except sender)
      socket.broadcast.emit('message', message);
      log('debug', `Broadcast message in ${namespace}`, {
        type: message.type,
        source: message.source,
      });
    } else if (Array.isArray(message.target)) {
      // Send to multiple specific targets
      message.target.forEach(targetId => {
        ns.to(targetId).emit('message', message);
      });
      log('debug', `Message sent to multiple targets in ${namespace}`, {
        type: message.type,
        targets: message.target,
      });
    } else {
      // Send to specific target
      ns.to(message.target).emit('message', message);
      log('debug', `Message sent to target in ${namespace}`, {
        type: message.type,
        target: message.target,
      });
    }
  }
  
  /**
   * Health check endpoint
   */
  systemNamespace.on('connection', (socket: any) => {
    socket.on('health-check', () => {
      const uptime = (Date.now() - stats.startTime.getTime()) / 1000;
      const messagesPerMinute = stats.lastMessageTime
        ? Math.round((stats.messagesProcessed / uptime) * 60)
        : 0;
      
      socket.emit('health-status', {
        id: `health_${Date.now()}`,
        type: EventTypes.HEALTH_CHECK,
        timestamp: new Date().toISOString(),
        source: 'socketio-server',
        data: {
          service: 'socketio-server',
          status: 'healthy',
          uptime_seconds: Math.round(uptime),
          active_connections: stats.activeConnections,
          messages_per_minute: messagesPerMinute,
          total_connections: stats.totalConnections,
          total_messages: stats.messagesProcessed,
          last_check: new Date().toISOString(),
        },
      });
    });
  });
  
  // Store Socket.IO instance in Strapi for access elsewhere
  (strapi as any).io = io;
  
  log('info', 'Socket.IO server ready', {
    activeConnections: stats.activeConnections,
  });
  
  return io;
}

/**
 * Shutdown Socket.IO server
 */
export function shutdownSocketIO(strapi: Core.Strapi) {
  const io = (strapi as any).io;
  if (io) {
    io.close(() => {
      console.log('[SocketIO] Server shutdown complete');
    });
  }
}
