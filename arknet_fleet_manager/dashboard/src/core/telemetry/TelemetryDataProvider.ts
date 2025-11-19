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

export class TelemetryDataProvider {
  private ws: WebSocket | null = null;
  private url: string;
  private token?: string;
  private reconnectAttempts = 0;
  // Infinite reconnects: no maxReconnectAttempts
  private listeners: Array<(vehicles: TelemetryVehicle[]) => void> = [];
  private statusListeners: Array<(state: TelemetryConnectionState) => void> = [];
  private vehicles: Map<string, TelemetryVehicle> = new Map();
  private state: TelemetryConnectionState = 'disconnected';
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private pingInterval: ReturnType<typeof setInterval> | null = null;

  constructor(baseUrl: string, token?: string) {
    // Convert http://localhost:5000 -> ws://localhost:5000/ws
    const wsUrl = baseUrl.replace(/^http/, 'ws').replace(/\/$/, '') + '/ws';
    this.url = token ? `${wsUrl}?token=${encodeURIComponent(token)}` : wsUrl;
    this.token = token;
  }

  connect() {
    if (this.ws && (this.ws.readyState === WebSocket.CONNECTING || this.ws.readyState === WebSocket.OPEN)) {
      console.log('TelemetryDataProvider: Already connecting or connected');
      return; // Already connecting or connected
    }

    console.log('TelemetryDataProvider: Connecting to', this.url);
    this.setState('connecting');
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      console.log('TelemetryDataProvider: Connected successfully');
      this.setState('connected');
      this.reconnectAttempts = 0;
      
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
      console.log('TelemetryDataProvider: Connection closed');
      this.stopPingInterval();
      if (this.state !== 'disconnected') {
        this.handleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('TelemetryDataProvider: WebSocket error', error);
      this.setState('error');
      // onclose will be called after onerror, which triggers reconnection
    };
  }

  disconnect() {
    console.log('TelemetryDataProvider: Disconnecting');
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }
    this.stopPingInterval();
    this.ws?.close();
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
}
