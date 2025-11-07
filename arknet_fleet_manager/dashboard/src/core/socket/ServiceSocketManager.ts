// Service-specific Socket.IO Manager following SOLID principles
import { BaseSocketManager } from './BaseSocketManager';
import { ISocketConfig, ISocketEventHandler } from '../../interfaces/socket';
import { ServiceStatus, ServiceState } from '../../providers/ServiceManager';

export interface ServiceEventData {
  service_name: string;
  timestamp: string;
  state: string;
  message?: string;
  port?: number;
  pid?: number;
}

export class ServiceSocketManager extends BaseSocketManager {
  constructor(config: ISocketConfig) {
    super(config);
  }

  protected setupCustomEventHandlers(): void {
    // Service-specific event handlers can be set up here
    // The base class already forwards all events to the event bus
  }

  /**
   * Subscribe to service status updates with automatic data transformation
   */
  subscribeToServiceUpdates(handler: (status: ServiceStatus) => void): () => void {
    const eventHandler: ISocketEventHandler<ServiceEventData> = {
      handle: (_event: string, data: ServiceEventData) => {
        console.debug('[ServiceSocketManager] Received raw service_status event', data);
        const serviceStatus: ServiceStatus = {
          name: data.service_name,
          state: data.state as ServiceState,
          port: data.port,
          message: data.message,
          pid: data.pid
        };
        console.debug('[ServiceSocketManager] Transformed service status', serviceStatus);
        handler(serviceStatus);
      },
      canHandle: () => true
    };

    // Subscribe to all service-related events
    // In a real implementation, you might want to filter by event type
    return this.subscribeToEvent('service_status', eventHandler);
  }

  /**
   * Subscribe to specific service updates
   */
  subscribeToSpecificService(serviceName: string, handler: (status: ServiceStatus) => void): () => void {
    const eventHandler: ISocketEventHandler<ServiceEventData> = {
      handle: (_event: string, data: ServiceEventData) => {
        if (data.service_name === serviceName) {
          const serviceStatus: ServiceStatus = {
            name: data.service_name,
            state: data.state as ServiceState,
            port: data.port,
            message: data.message,
            pid: data.pid
          };
          handler(serviceStatus);
        }
      },
      canHandle: (event: string, data: ServiceEventData) => {
        return event === 'service_status' && data.service_name === serviceName;
      }
    };

    return this.subscribeToEvent('service_status', eventHandler);
  }

  /**
   * Emit a service control command
   */
  emitServiceCommand(serviceName: string, command: 'start' | 'stop' | 'restart', params?: unknown): void {
    this.emit('service_command', {
      service_name: serviceName,
      command,
      params,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Request service status
   */
  requestServiceStatus(serviceName?: string): void {
    this.emit('get_service_status', {
      service_name: serviceName,
      timestamp: new Date().toISOString()
    });
  }

  /**
   * Request all services status
   */
  requestAllServicesStatus(): void {
    this.emit('get_all_services_status', {
      timestamp: new Date().toISOString()
    });
  }
}