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
      console.error('TelemetryDataProvider: WebSocket error', error);
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

    this.eventSource.onopen = () => {
      console.log('TelemetryDataProvider: Connected successfully via SSE');
      this.setState('connected');
      this.reconnectAttempts = 0;
    };

    this.eventSource.onmessage = (event) => {
      try {
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
        console.error('TelemetryDataProvider: Failed to parse SSE message', error);
      }
    };

    this.eventSource.onerror = (error) => {
      console.error('TelemetryDataProvider: SSE error', error);
      this.setState('error');
      
      // SSE automatically reconnects, but if it fails completely, try reconnecting
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        console.log('TelemetryDataProvider: SSE connection closed');
        if (this.state !== 'disconnected') {
          this.handleReconnect();
        }
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
    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'ping' }));
      }
    }, 30000); // Ping every 30 seconds
  }

  private stopPingInterval() {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
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
