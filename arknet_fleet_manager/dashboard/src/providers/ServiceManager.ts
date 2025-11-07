// ServiceManager.ts
// Centralized module to manage all services (gpscentcom_server, simulator, etc.)

interface ServiceStatus {
  name: string;
  state: 'stopped' | 'starting' | 'running' | 'healthy' | 'unhealthy' | 'failed';
  port?: number;
  message?: string;
  pid?: number;
}

interface ServiceManagerInterface {
  startService(serviceName: string): Promise<{ success: boolean; message: string; status?: ServiceStatus }>;
  stopService(serviceName: string): Promise<{ success: boolean; message: string }>;
  getServiceStatus(serviceName: string): Promise<{ success: boolean; status?: ServiceStatus; message?: string }>;
  getAllServiceStatuses(): Promise<{ success: boolean; statuses?: ServiceStatus[]; message?: string }>;
}

class ServiceManager implements ServiceManagerInterface {
  private readonly LAUNCHER_API_BASE = 'http://localhost:7000';
  private readonly SERVICES = [
    'strapi',
    'gpscentcom',
    'geospatial',
    'manifest',
    'vehicle_simulator',
    'commuter_service'
  ];

  constructor() {
    // Connect to launcher websocket for realtime events
    this.connectWebSocket();
  }

  private ws: WebSocket | null = null;
  private reconnectInterval = 2000; // ms
  private listeners: Array<(status: ServiceStatus) => void> = [];

  /**
   * Register a callback to receive realtime service status events from the launcher.
   */
  public onEvent(cb: (status: ServiceStatus) => void) {
    this.listeners.push(cb);
  }

  /**
   * Unregister a previously registered callback.
   */
  public offEvent(cb: (status: ServiceStatus) => void) {
    this.listeners = this.listeners.filter(l => l !== cb);
  }

  private connectWebSocket() {
    const url = this.LAUNCHER_API_BASE.replace(/^http/, 'ws') + '/events';

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        console.log('[ServiceManager] WebSocket connected to', url);
        // reset reconnect interval on success
        this.reconnectInterval = 2000;
      };

      this.ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data);
          // Launcher emits { service_name, timestamp, state, message, port, pid? }
          const status: ServiceStatus = {
            name: data.service_name || data.name,
            state: data.state,
            port: data.port,
            message: data.message,
            pid: data.pid
          };

          // notify listeners
          this.listeners.forEach(cb => {
            try { cb(status); } catch (err) { console.error('listener error', err); }
          });
        } catch (err) {
          console.error('[ServiceManager] Failed to parse websocket message', err);
        }
      };

      this.ws.onclose = (ev) => {
        console.warn('[ServiceManager] WebSocket closed, will reconnect in', this.reconnectInterval, 'ms');
        this.ws = null;
        setTimeout(() => this.connectWebSocket(), this.reconnectInterval);
        // exponential backoff up to 30s
        this.reconnectInterval = Math.min(30000, this.reconnectInterval * 1.5);
      };

      this.ws.onerror = (ev) => {
        console.error('[ServiceManager] WebSocket error', ev);
        // close socket to trigger reconnect
        try { this.ws?.close(); } catch (e) { /* ignore */ }
      };

    } catch (err) {
      console.error('[ServiceManager] Failed to create WebSocket', err);
      setTimeout(() => this.connectWebSocket(), this.reconnectInterval);
    }
  }

  async startService(serviceName: string): Promise<{ success: boolean; message: string; status?: ServiceStatus }> {
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
      
      // Return the event data from the launcher
      return {
        success: true,
        message: data.message || `${serviceName} is starting...`,
        status: {
          name: serviceName,
          state: data.state,
          port: data.port,
          message: data.message
        }
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

  async getAllServiceStatuses(): Promise<{ success: boolean; statuses?: ServiceStatus[]; message?: string }> {
    try {
      console.log('Fetching statuses for all services...');
      
      // Fetch status for each registered service
      const statusPromises = this.SERVICES.map(serviceName =>
        this.getServiceStatus(serviceName)
      );
      
      const results = await Promise.all(statusPromises);
      
      // Filter successful results and extract status
      const statuses = results
        .filter(result => result.success && result.status)
        .map(result => result.status!);

      return { success: true, statuses };
    } catch (error) {
      console.error('Failed to fetch statuses for all services:', error);
      return { success: false, message: 'Failed to fetch statuses for all services.' };
    }
  }
}

const serviceManager = new ServiceManager();
export default serviceManager;
