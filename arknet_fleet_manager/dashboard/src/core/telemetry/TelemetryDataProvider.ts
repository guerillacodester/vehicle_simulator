// TelemetryDataProvider: Standalone class for GPSCentCom WebSocket telemetry
// Connects to GPSCentCom server's /ws endpoint for real-time vehicle updates
// Compatible with GPSCentCom server WebSocket protocol (native WebSocket, not Socket.IO)

export type TelemetryVehicle = {
  deviceId: string;
  lat: number;
  lon: number;
  speed?: number;
  speed_m_s?: number;
  heading?: number;
  route?: string;
  vehicleReg?: string;
  driverId?: string;
  timestamp?: string;
  lastSeen?: string;
  [key: string]: unknown;
};

export type TelemetryConnectionState = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';
export type TelemetryConnectionType = 'websocket' | 'sse';

export class TelemetryDataProvider {
  private ws: WebSocket | null = null;
  private eventSource: EventSource | null = null;
  private baseUrl: string;
  private wsUrl: string;
  private sseUrl: string;
  private token?: string;
  private reconnectAttempts = 0;
  private wsFailures = 0; // Track consecutive WebSocket failures
  private useSSE = false; // Whether to use SSE fallback
  // Infinite reconnects: no maxReconnectAttempts
  private listeners: Array<(vehicles: TelemetryVehicle[]) => void> = [];
  private statusListeners: Array<(state: TelemetryConnectionState) => void> = [];
  private vehicles: Map<string, TelemetryVehicle> = new Map();
  private state: TelemetryConnectionState = 'disconnected';
  private connectionType: TelemetryConnectionType = 'websocket';
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private wsRetryTimeout: ReturnType<typeof setTimeout> | null = null;
  private lastPongTime: number = 0;
  private pongTimeout: ReturnType<typeof setTimeout> | null = null;

  constructor(baseUrl: string, token?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    // Convert http://localhost:5000 -> ws://localhost:5000/ws
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws';
    this.wsUrl = token ? `${wsUrl}?token=${encodeURIComponent(token)}` : wsUrl;
    // SSE endpoint: http://localhost:5000/sse?token=...
    this.sseUrl = token ? `${this.baseUrl}/sse?token=${encodeURIComponent(token)}` : `${this.baseUrl}/sse`;
    this.token = token;
  }

  connect() {
    // Try WebSocket first, fall back to SSE if WebSocket fails repeatedly
    if (this.wsFailures >= 3 && !this.useSSE) {
      console.log('TelemetryDataProvider: WebSocket failed multiple times, falling back to SSE');
      this.useSSE = true;
    }

    if (this.useSSE) {
      this.connectSSE();
      // Continue attempting WebSocket in background
      this.scheduleWebSocketRetry();
    } else {
      this.connectWebSocket();
    }
  }

  private connectWebSocket() {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.log('TelemetryDataProvider: Already connecting or connected via WebSocket');
      return;
    }

    console.log('TelemetryDataProvider: Connecting via WebSocket to', this.wsUrl);
    this.setState('connecting');
    this.connectionType = 'websocket';
    this.ws = new WebSocket(this.wsUrl);

    this.ws.onopen = () => {
      console.log('TelemetryDataProvider: Connected successfully via WebSocket');
      this.setState('connected');
      this.reconnectAttempts = 0;
      this.wsFailures = 0; // Reset failure counter on success
      
      // If we were using SSE, switch back to WebSocket
      if (this.useSSE) {
        console.log('TelemetryDataProvider: Switching from SSE to WebSocket');
        this.disconnectSSE();
        this.useSSE = false;
      }
      
      // Subscribe to telemetry topic to receive vehicle updates
      this.ws?.send(JSON.stringify({ type: 'subscribe', topic: 'telemetry' }));
      
      this.startPingInterval();
    };

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'snapshot' && Array.isArray(data.states)) {
          // Initial snapshot of all vehicles
          this.vehicles.clear();
          data.states.forEach((vehicle: TelemetryVehicle) => {
            this.vehicles.set(vehicle.deviceId, vehicle);
          });
          this.emit();
        } else if (data.type === 'update' && data.state) {
          // Real-time vehicle update from telemetry subscription
          this.vehicles.set(data.deviceId, data.state);
          this.emit();
        } else if (data.type === 'subscribed') {
          console.log('TelemetryDataProvider: Subscribed to topic:', data.topic);
        } else if (data.type === 'pong') {
          // Pong response to keepalive
          this.lastPongTime = Date.now();
          if (this.pongTimeout) {
            clearTimeout(this.pongTimeout);
            this.pongTimeout = null;
          }
        } else if (data.deviceId) {
          // Fallback: Single vehicle update (legacy format)
          this.vehicles.set(data.deviceId, data);
          this.emit();
        }
      } catch (error) {
        console.error('TelemetryDataProvider: Failed to parse message', error);
      }
    };

    this.ws.onclose = () => {
      console.log('TelemetryDataProvider: WebSocket connection closed');
      this.stopPingInterval();
      if (this.state !== 'disconnected') {
        this.wsFailures++;
        this.handleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.warn('TelemetryDataProvider: WebSocket connection failed, will retry automatically', { wsFailures: this.wsFailures + 1 });
      this.setState('error');
      this.wsFailures++;
      // onclose will be called after onerror, which triggers reconnection
    };
  }

  private connectSSE() {
    if (this.eventSource && (this.eventSource.readyState === EventSource.CONNECTING || this.eventSource.readyState === EventSource.OPEN)) {
      console.log('TelemetryDataProvider: Already connecting or connected via SSE');
      return;
    }

    console.log('TelemetryDataProvider: Connecting via SSE to', this.sseUrl);
    this.setState('connecting');
    this.connectionType = 'sse';
    this.eventSource = new EventSource(this.sseUrl);

    this.eventSource.onopen = async () => {
      console.log('TelemetryDataProvider: Connected successfully via SSE');
      this.setState('connected');
      this.reconnectAttempts = 0;
      
      // Fetch initial snapshot of vehicles for SSE connection
      try {
        const snapshotUrl = this.token 
          ? `${this.baseUrl}/snapshot?token=${encodeURIComponent(this.token)}`
          : `${this.baseUrl}/snapshot`;
        const response = await fetch(snapshotUrl);
        if (response.ok) {
          const snapshot = await response.json();
          if (Array.isArray(snapshot)) {
            this.vehicles.clear();
            snapshot.forEach((vehicle: TelemetryVehicle) => {
              this.vehicles.set(vehicle.deviceId, vehicle);
            });
            this.emit();
            console.log(`TelemetryDataProvider: Loaded ${snapshot.length} vehicles from snapshot`);
          }
        }
      } catch (error) {
        console.warn('TelemetryDataProvider: Failed to fetch initial snapshot for SSE', error);
      }
    };

    this.eventSource.onmessage = (event) => {
      try {
        // Skip empty or whitespace-only messages
        if (!event.data || !event.data.trim()) {
          return;
        }
        
        const data = JSON.parse(event.data);
        
        if (data.type === 'update' && data.state) {
          // Real-time vehicle update
          this.vehicles.set(data.deviceId, data.state);
          this.emit();
        } else if (data.deviceId) {
          // Fallback: Single vehicle update
          this.vehicles.set(data.deviceId, data);
          this.emit();
        }
      } catch (error) {
        console.warn('TelemetryDataProvider: Skipping invalid SSE message', { 
          data: event.data?.substring(0, 100),
          error: error instanceof Error ? error.message : String(error)
        });
      }
    };

    this.eventSource.onerror = (error) => {
      // SSE errors are expected during reconnection attempts
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        console.warn('TelemetryDataProvider: SSE connection closed, will retry automatically');
        if (this.state !== 'disconnected') {
          this.setState('error');
          this.handleReconnect();
        }
      } else {
        // Connection is still open or connecting, SSE will handle it
        console.warn('TelemetryDataProvider: SSE connection issue, automatic reconnection in progress');
      }
    };
  }

  private disconnectSSE() {
    if (this.eventSource) {
      console.log('TelemetryDataProvider: Disconnecting SSE');
      this.eventSource.close();
      this.eventSource = null;
    }
  }

  private scheduleWebSocketRetry() {
    // While using SSE, periodically try to reconnect WebSocket in background
    if (this.wsRetryTimeout) {
      clearTimeout(this.wsRetryTimeout);
    }
    
    this.wsRetryTimeout = setTimeout(() => {
      if (this.useSSE && this.state === 'connected') {
        console.log('TelemetryDataProvider: Attempting WebSocket reconnection in background');
        this.connectWebSocket();
      }
    }, 60000); // Try WebSocket every 60 seconds while using SSE
  }

  disconnect() {
    console.log('TelemetryDataProvider: Disconnecting');
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    if (this.wsRetryTimeout) {
      clearTimeout(this.wsRetryTimeout);
      this.wsRetryTimeout = null;
    }
    this.stopPingInterval();
    this.ws?.close();
    this.disconnectSSE();
    this.setState('disconnected');
  }

  private handleReconnect() {
    this.setState('reconnecting');
    this.reconnectAttempts++;
    // Always retry, no max limit
    const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`TelemetryDataProvider: Reconnecting (attempt ${this.reconnectAttempts}) in ${delay}ms`);
    this.reconnectTimeout = setTimeout(() => this.connect(), delay);
  }

  private startPingInterval() {
    this.lastPongTime = Date.now();
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Check if we've received a pong recently
        const timeSinceLastPong = Date.now() - this.lastPongTime;
        if (timeSinceLastPong > 90000) { // No pong for 90 seconds
          console.warn('TelemetryDataProvider: WebSocket connection appears dead, reconnecting');
          this.ws.close();
          return;
        }
        
        this.ws.send(JSON.stringify({ type: 'ping' }));
        
        // Set timeout for pong response
        if (this.pongTimeout) {
          clearTimeout(this.pongTimeout);
        }
        this.pongTimeout = setTimeout(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            console.warn('TelemetryDataProvider: No pong received, connection may be dead');
            this.ws.close();
          }
        }, 10000); // Wait 10 seconds for pong
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
    if (this.pongTimeout) {
      clearTimeout(this.pongTimeout);
      this.pongTimeout = null;
    }
  }

  subscribe(listener: (vehicles: TelemetryVehicle[]) => void) {
    this.listeners.push(listener);
    listener(Array.from(this.vehicles.values()));
    return () => {
      this.listeners = this.listeners.filter(l => l !== listener);
    };
  }

  onStatus(listener: (state: TelemetryConnectionState) => void) {
    this.statusListeners.push(listener);
    listener(this.state);
    return () => {
      this.statusListeners = this.statusListeners.filter(l => l !== listener);
    };
  }

  private emit() {
    const vehiclesArray = Array.from(this.vehicles.values());
    this.listeners.forEach(l => l(vehiclesArray));
  }

  private setState(state: TelemetryConnectionState) {
    this.state = state;
    this.statusListeners.forEach(l => l(state));
  }

  getVehicles(): TelemetryVehicle[] {
    return Array.from(this.vehicles.values());
  }

  getState() {
    return this.state;
  }

  getConnectionType(): TelemetryConnectionType {
    return this.connectionType;
  }

  getDiagnostics() {
    return {
      state: this.state,
      connectionType: this.connectionType,
      reconnectAttempts: this.reconnectAttempts,
      wsFailures: this.wsFailures,
      useSSE: this.useSSE,
      vehicleCount: this.vehicles.size
    };
  }
}
