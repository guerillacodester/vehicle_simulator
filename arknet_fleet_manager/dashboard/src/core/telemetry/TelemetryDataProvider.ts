import { ErrorHandler } from '@/lib/errors/ErrorHandler';
import { ErrorCodes } from '@/lib/errors/ErrorCodes';
import { RetryStrategy, CircuitState } from '@/lib/errors/RetryStrategy';
import { ErrorRecovery } from '@/lib/errors/ErrorRecovery';
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
  private refreshToken?: () => Promise<string>;
  private reconnectAttempts = 0;
  private wsFailures = 0; // Track consecutive WebSocket failures
  private useSSE = false; // Whether to use SSE fallback
  // Infinite reconnects: no maxReconnectAttempts
  private listeners: Array<(vehicles: TelemetryVehicle[]) => void> = [];
  private statusListeners: Array<(state: TelemetryConnectionState, error?: any) => void> = [];
  private vehicles: Map<string, TelemetryVehicle> = new Map();
  private state: TelemetryConnectionState = 'disconnected';
  private connectionType: TelemetryConnectionType = 'websocket';
  private reconnectTimeout: ReturnType<typeof setTimeout> | null = null;
  private pingInterval: ReturnType<typeof setInterval> | null = null;
  private wsRetryTimeout: ReturnType<typeof setTimeout> | null = null;
  private lastPongTime: number = 0;
  private pongTimeout: ReturnType<typeof setTimeout> | null = null;
  private lastError: any = null;
  
  // Enhanced error handling and retry logic
  private retryStrategy: RetryStrategy;
  private errorMetrics = {
    totalErrors: 0,
    errorsByType: new Map<string, number>(),
    lastErrorAt: 0,
    recoveryAttempts: 0,
    successfulRecoveries: 0,
  };

  constructor(baseUrl: string, token?: string, refreshToken?: () => Promise<string>) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
    this.token = token;
    this.refreshToken = refreshToken;
    this.updateUrls();
    
    // Initialize retry strategy with circuit breaker
    this.retryStrategy = new RetryStrategy({
      maxRetries: -1, // Infinite retries
      initialDelay: 1000,
      maxDelay: 30000,
      backoffMultiplier: 2,
      jitterFactor: 0.1,
      circuitBreakerThreshold: 5,
      circuitBreakerTimeout: 60000,
    });
  }

  private updateUrls() {
    // Don't include token in URL - browser will automatically send httpOnly cookie
    const wsUrl = this.baseUrl.replace(/^http/, 'ws') + '/ws';
    this.wsUrl = wsUrl;
    this.sseUrl = `${this.baseUrl}/sse`;
  }

  // Call this to update token and rebuild URLs
  async setToken(newToken: string) {
    this.token = newToken;
    this.updateUrls();
    // Optionally reconnect with new token
    this.disconnect();
    this.connect();
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
      this.lastError = null;
      
      // Record successful recovery
      this.retryStrategy.recordSuccess();
      this.errorMetrics.successfulRecoveries++;
      
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
          this.vehicles.clear();
          data.states.forEach((vehicle: TelemetryVehicle) => {
            this.vehicles.set(vehicle.deviceId, vehicle);
          });
          this.emit();
        } else if (data.type === 'update' && data.state) {
          this.vehicles.set(data.deviceId, data.state);
          this.emit();
        } else if (data.type === 'subscribed') {
          console.log('TelemetryDataProvider: Subscribed to topic:', data.topic);
        } else if (data.type === 'pong') {
          this.lastPongTime = Date.now();
          if (this.pongTimeout) {
            clearTimeout(this.pongTimeout);
            this.pongTimeout = null;
          }
        } else if (data.deviceId) {
          this.vehicles.set(data.deviceId, data);
          this.emit();
        }
      } catch (error) {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.DATA_PARSE_ERROR,
          message: 'Failed to parse WebSocket message',
          details: { event, error },
        });
        this.trackError(this.lastError);
        console.warn('TelemetryDataProvider: Data parse error, continuing connection');
        // Don't disconnect on parse error, just log and continue
      }
    };

    this.ws.onclose = async (event) => {
      console.log('TelemetryDataProvider: WebSocket connection closed');
      this.stopPingInterval();
      
      // Handle token expiration
      if (event && event.code === 4001 && this.refreshToken) {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.TOKEN_EXPIRED,
          message: 'Token expired',
          details: { event },
        });
        this.trackError(this.lastError);
        
        const recovery = ErrorRecovery.getRecoveryAction(this.lastError);
        console.log(`TelemetryDataProvider: ${recovery.message}`);
        
        try {
          const newToken = await this.refreshToken();
          await this.setToken(newToken);
          this.errorMetrics.successfulRecoveries++;
          return;
        } catch (err) {
          this.lastError = ErrorHandler.handle({
            code: ErrorCodes.AUTH_ERROR,
            message: 'Token refresh failed',
            details: { event, err },
          });
          this.trackError(this.lastError);
          this.retryStrategy.recordFailure();
          this.setState('error', this.lastError);
          return;
        }
      }
      
      // Handle normal connection close
      if (this.state !== 'disconnected') {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.NETWORK_ERROR,
          message: 'WebSocket connection closed',
          details: { event },
        });
        this.trackError(this.lastError);
        this.wsFailures++;
        this.retryStrategy.recordFailure();
        this.handleReconnect();
      }
    };

    this.ws.onerror = (event) => {
      this.lastError = ErrorHandler.handle({
        code: ErrorCodes.NETWORK_ERROR,
        message: 'WebSocket error occurred',
        details: { event },
      });
      this.trackError(this.lastError);
      console.error('TelemetryDataProvider: WebSocket error', this.lastError);
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
      this.lastError = null;
      this.retryStrategy.recordSuccess();
      this.errorMetrics.successfulRecoveries++;
      
      // Fetch initial snapshot of vehicles for SSE connection
      try {
        const snapshotUrl = `${this.baseUrl}/snapshot`;
        // Include credentials to send httpOnly cookie
        const response = await fetch(snapshotUrl, { credentials: 'include' });
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
        if (!event.data || !event.data.trim()) {
          return;
        }
        const data = JSON.parse(event.data);
        if (data.type === 'update' && data.state) {
          this.vehicles.set(data.deviceId, data.state);
          this.emit();
        } else if (data.deviceId) {
          this.vehicles.set(data.deviceId, data);
          this.emit();
        }
      } catch (error) {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.DATA_PARSE_ERROR,
          message: 'Skipping invalid SSE message',
          details: { event, error },
        });
        this.trackError(this.lastError);
        console.warn('TelemetryDataProvider: SSE data parse error, continuing connection');
      }
    };

    this.eventSource.onerror = async (error) => {
      if (this.refreshToken && error && error.status === 401) {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.TOKEN_EXPIRED,
          message: 'SSE token expired',
          details: { error },
        });
        this.trackError(this.lastError);
        
        const recovery = ErrorRecovery.getRecoveryAction(this.lastError);
        console.log(`TelemetryDataProvider: ${recovery.message}`);
        
        try {
          const newToken = await this.refreshToken();
          await this.setToken(newToken);
          this.errorMetrics.successfulRecoveries++;
          return;
        } catch (err) {
          this.lastError = ErrorHandler.handle({
            code: ErrorCodes.AUTH_ERROR,
            message: 'SSE token refresh failed',
            details: { error, err },
          });
          this.trackError(this.lastError);
          this.retryStrategy.recordFailure();
          this.setState('error', this.lastError);
          return;
        }
      }
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.NETWORK_ERROR,
          message: 'SSE connection closed',
          details: { error },
        });
        this.trackError(this.lastError);
        if (this.state !== 'disconnected') {
          this.retryStrategy.recordFailure();
          this.setState('error', this.lastError);
          this.handleReconnect();
        }
      } else {
        this.lastError = ErrorHandler.handle({
          code: ErrorCodes.NETWORK_ERROR,
          message: 'SSE connection issue',
          details: { error },
        });
        this.trackError(this.lastError);
        console.warn('TelemetryDataProvider: SSE connection issue', error);
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
    // Check if we can retry based on circuit breaker
    if (!this.retryStrategy.canRetry()) {
      console.warn('TelemetryDataProvider: Circuit breaker preventing reconnection');
      this.setState('error', this.lastError);
      
      // Schedule a check to see if circuit breaker has closed
      this.reconnectTimeout = setTimeout(() => {
        if (this.retryStrategy.canRetry()) {
          this.handleReconnect();
        }
      }, 10000);
      return;
    }

    this.setState('reconnecting');
    this.reconnectAttempts++;
    this.errorMetrics.recoveryAttempts++;
    this.retryStrategy.recordAttempt();
    
    const delay = this.retryStrategy.getNextDelay();
    const stats = this.retryStrategy.getStats();
    
    console.log(`TelemetryDataProvider: Reconnecting (attempt ${this.reconnectAttempts}, circuit: ${stats.circuitState}) in ${delay}ms`);
    
    // Log recovery action
    if (this.lastError) {
      const recovery = ErrorRecovery.getRecoveryAction(this.lastError);
      console.log(`TelemetryDataProvider: Recovery action: ${recovery.type} - ${recovery.message}`);
    }
    
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

  private setState(state: TelemetryConnectionState, error?: any) {
    this.state = state;
    this.statusListeners.forEach(l => l(state, error));
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
    const retryStats = this.retryStrategy.getStats();
    
    return {
      state: this.state,
      connectionType: this.connectionType,
      reconnectAttempts: this.reconnectAttempts,
      wsFailures: this.wsFailures,
      useSSE: this.useSSE,
      vehicleCount: this.vehicles.size,
      // Enhanced diagnostics
      retryStats,
      errorMetrics: {
        totalErrors: this.errorMetrics.totalErrors,
        errorsByType: Object.fromEntries(this.errorMetrics.errorsByType),
        lastErrorAt: this.errorMetrics.lastErrorAt,
        recoveryAttempts: this.errorMetrics.recoveryAttempts,
        successfulRecoveries: this.errorMetrics.successfulRecoveries,
        recoveryRate: this.errorMetrics.recoveryAttempts > 0
          ? (this.errorMetrics.successfulRecoveries / this.errorMetrics.recoveryAttempts * 100).toFixed(1) + '%'
          : 'N/A',
      },
      lastError: this.lastError ? {
        code: this.lastError.code,
        message: this.lastError.message,
        timestamp: this.errorMetrics.lastErrorAt,
      } : null,
    };
  }

  // Track error for metrics
  private trackError(error: any) {
    this.errorMetrics.totalErrors++;
    this.errorMetrics.lastErrorAt = Date.now();
    
    const errorType = error.code || 'UNKNOWN';
    const count = this.errorMetrics.errorsByType.get(errorType) || 0;
    this.errorMetrics.errorsByType.set(errorType, count + 1);
    
    // Log structured error for monitoring
    console.error('TelemetryDataProvider: Error tracked', {
      code: error.code,
      message: error.message,
      totalErrors: this.errorMetrics.totalErrors,
      errorsByType: Object.fromEntries(this.errorMetrics.errorsByType),
      retryStats: this.retryStrategy.getStats(),
    });
  }

  // Get error recovery recommendation for UI
  getErrorRecovery() {
    if (!this.lastError) return null;
    
    return {
      action: ErrorRecovery.getRecoveryAction(this.lastError),
      isTransient: ErrorRecovery.isTransientError(this.lastError),
      requiresUserAction: ErrorRecovery.requiresUserAction(this.lastError),
      userMessage: ErrorRecovery.getUserMessage(this.lastError),
      recommendedAction: ErrorRecovery.getRecommendedAction(this.lastError),
    };
  }
}
