// ServiceManager.ts
// Centralized module to manage all services (gpscentcom_server, simulator, etc.)

import { ServiceSocketManager } from '../core/socket';
import { SocketConnectionState, SocketConnectionStatus } from '../interfaces/socket';

export enum ServiceState {
  STOPPED = 'stopped',
  STARTING = 'starting',
  RUNNING = 'running',
  HEALTHY = 'healthy',
  UNHEALTHY = 'unhealthy',
  FAILED = 'failed',
}

export enum ConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error'
}

export interface ConnectionStatus {
  state: ConnectionState;
  message: string;
  lastConnected?: Date;
}

export interface ServiceMetadata {
  display_name?: string;
  description?: string;
  category?: string;
  icon?: string;
}

export interface ServiceStatus {
  name: string;
  state: ServiceState;
  port?: number;
  message?: string;
  pid?: number;
  // UI Metadata
  display_name?: string;
  description?: string;
  category?: string;
  icon?: string;
}

interface ServiceManagerInterface {
  startService(serviceName: string): Promise<{ success: boolean; message: string }>;
  stopService(serviceName: string): Promise<{ success: boolean; message: string }>;
  getServiceStatus(serviceName: string): Promise<{ success: boolean; status?: ServiceStatus; message?: string }>;
  getAllServiceStatuses(): Promise<{ success: boolean; statuses?: ServiceStatus[]; message?: string }>;
}

class ServiceManager implements ServiceManagerInterface {
  private readonly LAUNCHER_API_BASE = 'http://localhost:7000';
  private services: string[] = [];
  private servicesLoaded = false;

  // Socket.IO manager for real-time communication
  private socketManager: ServiceSocketManager;
  private listeners: Array<(status: ServiceStatus) => void> = [];
  private serviceListeners: Record<string, Array<(status: ServiceStatus) => void>> = {};

  private async loadServices() {
    try {
      const response = await fetch(`${this.LAUNCHER_API_BASE}/services`);
      if (response.ok) {
        const servicesData: Array<{name: string}> = await response.json();
        // Extract service names from the response
        this.services = servicesData.map(service => service.name);
        this.servicesLoaded = true;
        console.log('[ServiceManager] Loaded services:', this.services);
      } else {
        console.warn('[ServiceManager] Failed to load services from API');
        // Don't use hardcoded fallback - services should be loaded from launcher
        this.services = [];
        this.servicesLoaded = true;
      }
    } catch (error) {
      console.warn('[ServiceManager] Error loading services:', error);
      // Don't use hardcoded fallback - services should be loaded from launcher
      this.services = [];
      this.servicesLoaded = true;
    }
  }

    constructor() {
    // Initialize Socket.IO manager
    this.socketManager = new ServiceSocketManager({
      url: this.LAUNCHER_API_BASE,
      options: {
        transports: ['websocket', 'polling'], // Prefer websocket, fallback to polling
        timeout: 20000,
        reconnection: true,
        reconnectionAttempts: 0, // Infinite attempts
        reconnectionDelay: 1000,
        forceNew: true, // Always create new connection
        autoConnect: false, // We'll connect manually after setup
        auth: { // Add authentication
          token: 'dashboard-client'
        },
        path: '/socket.io' // Client needs leading slash
      }
    });
    
    // Set up service status event handling
    this.setupServiceEventHandling();

    // Connect to the launcher
    this.socketManager.connect().catch(err => {
      console.error('[ServiceManager] Failed to connect to launcher:', err);
    });

    // Load available services from the API
    this.loadServices();
  }

  private setupServiceEventHandling(): void {
    // Subscribe to all service status updates
    this.socketManager.subscribeToServiceUpdates((status: ServiceStatus) => {
      console.debug('[ServiceManager] socket update received', status);
      // Notify general listeners
      this.listeners.forEach(cb => {
        try { cb(status); } catch (err) { console.error('listener error', err); }
      });

      // Notify service-specific listeners
      if (this.serviceListeners[status.name]) {
        this.serviceListeners[status.name].forEach(cb => {
          try { cb(status); } catch (err) { console.error('service listener error', err); }
        });
      }
    });
  }

  /**
   * Register a callback to receive realtime service status events from the launcher.
   */
  public onEvent(cb: (status: ServiceStatus) => void) {
    this.listeners.push(cb);
  }

  /**
   * Register a callback to receive connection status events.
   */
  public onConnectionEvent(cb: (status: ConnectionStatus) => void) {
    // Convert Socket.IO connection status to our ConnectionStatus format
    const connectionHandler = (socketStatus: SocketConnectionStatus) => {
      const status: ConnectionStatus = {
        state: this.mapSocketStateToConnectionState(socketStatus),
        message: socketStatus.message || '',
        lastConnected: socketStatus.lastConnected || new Date()
      };
      cb(status);
    };

    this.socketManager.onConnectionChange(connectionHandler);
  }

  /**
   * Unregister a connection status callback.
   */
  public offConnectionEvent(callback: (status: ConnectionStatus) => void) {
    // Create a wrapper that maps ConnectionStatus to SocketConnectionStatus
    const socketHandler = (socketStatus: SocketConnectionStatus) => {
      callback({
        state: this.mapSocketStateToConnectionState(socketStatus),
        message: socketStatus.message || '',
        lastConnected: socketStatus.lastConnected
      });
    };
    this.socketManager.offConnectionChange(socketHandler);
    // Note: This is a simplified implementation
    // In a full implementation, you'd need to track the wrapper functions
    this.socketManager.offConnectionChange(() => {}); // Placeholder
  }

  /**
   * Get current connection status.
   */
  public getConnectionStatus(): ConnectionStatus {
    const socketStatus = this.socketManager.getConnectionStatus();
    return {
      state: this.mapSocketStateToConnectionState(socketStatus),
      message: socketStatus.message,
      lastConnected: socketStatus.lastConnected
    };
  }

  private mapSocketStateToConnectionState(socketStatus: SocketConnectionStatus): ConnectionState {
    const socketState = socketStatus.state;
    switch (socketState) {
      case SocketConnectionState.CONNECTING:
        return ConnectionState.CONNECTING;
      case SocketConnectionState.CONNECTED:
        return ConnectionState.CONNECTED;
      case SocketConnectionState.DISCONNECTED:
        return ConnectionState.DISCONNECTED;
      case SocketConnectionState.ERROR:
        return ConnectionState.ERROR;
      case SocketConnectionState.RECONNECTING:
        // Map reconnecting to connecting state since ConnectionState doesn't have RECONNECTING
        return ConnectionState.CONNECTING;
      default:
        return ConnectionState.ERROR;
    }
  }

  /**
   * Unregister a previously registered callback.
   */
  public offEvent(cb: (status: ServiceStatus) => void) {
    this.listeners = this.listeners.filter(l => l !== cb);
  }

  /**
   * Force reload the services list from the launcher API.
   * Useful when services have been added/removed.
   */
  public async reloadServices(): Promise<void> {
    await this.loadServices();
  }

  /**
   * Unregister a service-specific callback.
   */
  public offServiceEvent(serviceName: string, cb: (status: ServiceStatus) => void) {
    if (this.serviceListeners[serviceName]) {
      this.serviceListeners[serviceName] = this.serviceListeners[serviceName].filter(l => l !== cb);
    }
  }

  async startService(serviceName: string): Promise<{ success: boolean; message: string }> {
    try {
      console.log(`Starting ${serviceName} via launcher API...`);

      const response = await fetch(`${this.LAUNCHER_API_BASE}/services/${serviceName}/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      // Don't return status - let Socket.IO events handle all status updates
      return {
        success: true,
        message: data.message || `${serviceName} start initiated`
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to start ${serviceName}:`, errorMessage);
      return {
        success: false,
        message: `Failed to start ${serviceName}: ${errorMessage}`
      };
    }
  }

  async stopService(serviceName: string): Promise<{ success: boolean; message: string }> {
    try {
      console.log(`Stopping ${serviceName} via launcher API...`);

      const response = await fetch(`${this.LAUNCHER_API_BASE}/services/${serviceName}/stop`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        message: data.message || `${serviceName} stopped successfully.`
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to stop ${serviceName}:`, errorMessage);
      return {
        success: false,
        message: `Failed to stop ${serviceName}: ${errorMessage}`
      };
    }
  }

  async getServiceStatus(serviceName: string): Promise<{ success: boolean; status?: ServiceStatus; message?: string }> {
    try {
      console.log(`Fetching status for ${serviceName}...`);

      const response = await fetch(`${this.LAUNCHER_API_BASE}/services/${serviceName}/status`);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        status: {
          name: data.name,
          state: data.state,
          port: data.port,
          message: data.message,
          pid: data.pid
        }
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error(`Failed to fetch status for ${serviceName}:`, errorMessage);
      return {
        success: false,
        message: `Failed to fetch status for ${serviceName}: ${errorMessage}`
      };
    }
  }

  async reloadConfig(): Promise<{ success: boolean; message: string; services?: string[] }> {
    try {
      console.log('Reloading launcher configuration...');

      const response = await fetch(`${this.LAUNCHER_API_BASE}/reload-config`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        // Reload the services list
        await this.loadServices();
        return {
          success: true,
          message: 'Configuration reloaded successfully',
          services: data.services
        };
      } else {
        throw new Error(data.error || 'Failed to reload configuration');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Failed to reload config:', errorMessage);
      return {
        success: false,
        message: `Failed to reload configuration: ${errorMessage}`
      };
    }
  }

  async getAllServiceStatuses(): Promise<{ success: boolean; statuses?: ServiceStatus[]; message?: string }> {
    try {
      console.log('Fetching statuses for all services...');

      // Ensure services are loaded
      if (!this.servicesLoaded) {
        await this.loadServices();
      }

      // Fetch status for each registered service
      const statusPromises = this.services!.map((serviceName: string) =>
        this.getServiceStatus(serviceName)
      );

      const results = await Promise.all(statusPromises);

      // Filter successful results and extract status
      const statuses = results
        .filter((result: { success: boolean; status?: ServiceStatus; message?: string }) => result.success && result.status)
        .map((result: { success: boolean; status?: ServiceStatus; message?: string }) => result.status!);

      return { success: true, statuses };
    } catch (error) {
      console.error('Failed to fetch statuses for all services:', error);
      return { success: false, message: 'Failed to fetch statuses for all services.' };
    }
  }

  /**
   * Cleanup method to stop connections.
   */
  public destroy() {
    this.socketManager.disconnect().catch((err: unknown) => {
      console.error('[ServiceManager] Error disconnecting:', err);
    });
  }
}

const serviceManager = new ServiceManager();
export { ServiceManager };
export default serviceManager;
