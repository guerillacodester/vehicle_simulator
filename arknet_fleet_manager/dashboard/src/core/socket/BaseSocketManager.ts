// Base Socket.IO Manager following SOLID principles
import { io, Socket } from 'socket.io-client';
import { createComponentLogger } from '../../lib/observability';
import {
  ISocketConnectionManager,
  ISocketReconnectionStrategy,
  ISocketConfig,
  SocketConnectionState,
  SocketConnectionStatus,
  ISocketEventHandler
} from '../../interfaces/socket';
import { SocketEventBus } from './SocketEventBus';

export class ExponentialBackoffReconnectionStrategy implements ISocketReconnectionStrategy {
  private readonly maxAttempts: number;
  private readonly baseDelay: number;
  private readonly maxDelay: number;

  constructor(maxAttempts = 10, baseDelay = 1000, maxDelay = 30000) {
    this.maxAttempts = maxAttempts;
    this.baseDelay = baseDelay;
    this.maxDelay = maxDelay;
  }

  shouldReconnect(): boolean {
    // Always attempt reconnection for network errors
    return true;
  }

  getReconnectDelay(attempt: number): number {
    if (attempt >= this.maxAttempts) {
      return 0; // Stop reconnecting
    }
    const delay = Math.min(this.baseDelay * Math.pow(2, attempt), this.maxDelay);
    return delay + Math.random() * 1000; // Add jitter
  }

  reset(): void {
    // Reset logic if needed
  }
}

export abstract class BaseSocketManager implements ISocketConnectionManager {
  protected socket: Socket | null = null;
  protected connectionState: SocketConnectionState = SocketConnectionState.DISCONNECTED;
  protected lastConnected: Date | null = null;
  protected reconnectAttempts = 0;
  protected connectionListeners: Array<(status: SocketConnectionStatus) => void> = [];
  protected eventBus = new SocketEventBus<unknown>();
  // No polling: remove custom heartbeat/backoff timers; rely on Socket.IO reconnection
  private readonly logger = createComponentLogger('SocketManager');
  // Heartbeat configuration (tuned for immediate detection)
  private heartbeatTimer?: ReturnType<typeof setInterval>;
  private readonly heartbeatIntervalMs: number = 3000; // 3s cadence for faster detection
  private missedHeartbeats = 0;
  private readonly maxMissedHeartbeats = 1; // trigger reconnect after just 1 miss (~3s response)
  private heartbeatAckTimeouts: Map<number, ReturnType<typeof setTimeout>> = new Map();
  private onHeartbeatAckBound?: (payload: { ts: number }) => void;
  private boundOnlineHandler?: () => void;
  private boundVisibilityHandler?: () => void;

  constructor(
    protected config: ISocketConfig,
    protected reconnectionStrategy: ISocketReconnectionStrategy = new ExponentialBackoffReconnectionStrategy()
  ) {}
  
  private attachWindowConnectivityHooks(): void {
    if (typeof window === 'undefined') return;
    if (!this.boundOnlineHandler) {
      this.boundOnlineHandler = () => {
        // If browser regained connectivity, try to reconnect immediately (no polling)
        if (this.socket && !this.socket.connected) {
          try { this.socket.connect(); } catch {}
        }
      };
      window.addEventListener('online', this.boundOnlineHandler);
    }
    if (!this.boundVisibilityHandler) {
      this.boundVisibilityHandler = () => {
        if (document.visibilityState === 'visible' && this.socket && !this.socket.connected) {
          try { this.socket.connect(); } catch {}
        }
      };
      window.addEventListener('visibilitychange', this.boundVisibilityHandler);
    }
  }
  
  private detachWindowConnectivityHooks(): void {
    if (typeof window === 'undefined') return;
    if (this.boundOnlineHandler) {
      window.removeEventListener('online', this.boundOnlineHandler);
      this.boundOnlineHandler = undefined;
    }
    if (this.boundVisibilityHandler) {
      window.removeEventListener('visibilitychange', this.boundVisibilityHandler);
      this.boundVisibilityHandler = undefined;
    }
  }

  async connect(): Promise<void> {
    if (this.socket?.connected) {
      this.logger.debug('Already connected');
      return;
    }

    // If we're already trying to connect, don't create a new attempt
    if (this.connectionState === SocketConnectionState.CONNECTING) {
      this.logger.debug('Connection attempt already in progress');
      return;
    }
  this.logger.info('Connecting', { metadata: { url: this.config.url } });
    this.updateConnectionState(SocketConnectionState.CONNECTING);

    try {
      // Clean up existing socket if any
      if (this.socket) {
        this.socket.removeAllListeners();
        this.socket.disconnect();
        this.socket = null;
      }

  this.socket = io(this.config.url, this.config.options);

      this.setupSocketEventHandlers();
      this.setupCustomEventHandlers();
  this.attachWindowConnectivityHooks();
  this.startHeartbeat();

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          this.logger.error('Connection timeout', new Error('timeout'), { metadata: { timeoutMs: this.config.options?.timeout || 10000 } });
          this.updateConnectionState(SocketConnectionState.DISCONNECTED);
          reject(new Error('Connection timeout'));
        }, this.config.options?.timeout || 10000);

        this.socket!.once('connect', () => {
          this.logger.info('Connected');
          clearTimeout(timeout);
          this.reconnectionStrategy.reset();
          this.reconnectAttempts = 0;
          
          // Built-in reconnection paths only
          
          this.updateConnectionState(SocketConnectionState.CONNECTED);
          resolve();
        });

        this.socket!.once('connect_error', (error) => {
          this.logger.warn('Connection error', { metadata: { errorMessage: (error as Error).message || String(error) } });
          clearTimeout(timeout);
          this.handleConnectionError(error);
          reject(error);
        });

        // Manually trigger connection if autoConnect is false
        if (this.config.options?.autoConnect === false) {
          this.logger.debug('Manual connect trigger (autoConnect false)');
          this.socket!.connect();
        }
      });
    } catch (error) {
      this.logger.error('Exception during connect', error as Error);
      this.handleConnectionError(error as Error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    // Intentional disconnect, no polling cleanup needed
    this.detachWindowConnectivityHooks();
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.stopHeartbeat();
    this.updateConnectionState(SocketConnectionState.DISCONNECTED);
    this.reconnectionStrategy.reset();
    this.reconnectAttempts = 0;
  }

  emit(event: string, data?: unknown): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      this.logger.warn('Emit failed - not connected', { metadata: { event } });
    }
  }

  on(event: string, handler: (data: unknown) => void): void {
    const eventHandler: ISocketEventHandler<unknown> = {
      handle: (_event: string, data: unknown) => handler(data),
      canHandle: () => true
    };

    this.eventBus.subscribe(event, eventHandler);

    if (this.socket) {
      this.socket.on(event, handler);
    }
  }

  off(event: string, handler?: (data: unknown) => void): void {
    if (handler) {
      // For specific handler removal, we need to find the wrapper
      // This is a limitation - we can't easily remove specific handlers
      // Consider using the event bus directly for more control
      if (this.socket) {
        this.socket.off(event, handler);
      }
    } else {
      this.eventBus.unsubscribe(event);
      if (this.socket) {
        this.socket.off(event);
      }
    }
  }

  getConnectionStatus(): SocketConnectionStatus {
    return {
      state: this.connectionState,
      message: this.getConnectionMessage(),
      lastConnected: this.lastConnected || undefined,
      reconnectAttempts: this.reconnectAttempts
    };
  }

  onConnectionChange(handler: (status: SocketConnectionStatus) => void): void {
    this.connectionListeners.push(handler);
    // Send current status immediately
    handler(this.getConnectionStatus());
  }

  offConnectionChange(handler: (status: SocketConnectionStatus) => void): void {
    const index = this.connectionListeners.indexOf(handler);
    if (index > -1) {
      this.connectionListeners.splice(index, 1);
    }
  }

  /**
   * Subscribe to specific events with a custom event handler
   * This provides more control than the basic on/off methods
   */
  subscribeToEvent(event: string, handler: ISocketEventHandler<unknown>): () => void {
    return this.eventBus.subscribe(event, handler);
  }

  /**
   * Unsubscribe from specific events
   */
  unsubscribeFromEvent(event: string, handler?: ISocketEventHandler<unknown>): void {
    this.eventBus.unsubscribe(event, handler);
  }

  /**
   * Get the event bus for advanced event management
   */
  getEventBus(): SocketEventBus<unknown> {
    return this.eventBus;
  }

  protected abstract setupCustomEventHandlers(): void;

  protected updateConnectionState(state: SocketConnectionState): void {
    if (this.connectionState !== state) {
      this.connectionState = state;
      if (state === SocketConnectionState.CONNECTED) {
        this.lastConnected = new Date();
      }

      const status = this.getConnectionStatus();
      this.connectionListeners.forEach(cb => {
        try { cb(status); } catch (err) { console.error('connection listener error', err); }
      });
    }
  }

  protected getConnectionMessage(): string {
    switch (this.connectionState) {
      case SocketConnectionState.CONNECTING:
        return 'Connecting to launcher...';
      case SocketConnectionState.CONNECTED:
        return 'Connected to launcher';
      case SocketConnectionState.DISCONNECTED:
        return 'Disconnected - Service controls disabled';
      case SocketConnectionState.ERROR:
        return 'Connection error - Retrying...';
      case SocketConnectionState.RECONNECTING:
        return `Reconnecting to launcher... (attempt ${this.reconnectAttempts})`;
      default:
        return 'Unknown connection state';
    }
  }

  private setupSocketEventHandlers(): void {
    if (!this.socket) return;

    // Set up socket event handlers that publish to the event bus
    this.socket.on('connect', () => {
      this.logger.debug('Low-level connect event');
      this.reconnectionStrategy.reset();
      this.reconnectAttempts = 0;
      this.updateConnectionState(SocketConnectionState.CONNECTED);
    });

    this.socket.on('disconnect', (reason) => {
      this.logger.info('Disconnected', { metadata: { reason } });
      this.updateConnectionState(SocketConnectionState.DISCONNECTED);
      this.stopHeartbeat();

      if (reason === 'io client disconnect') {
        // Client asked to disconnect; do not auto-reconnect
        this.logger.debug('Client-initiated disconnect - not reconnecting');
        return;
      }
      if (reason === 'io server disconnect') {
        // Per Socket.IO docs: server disconnect requires manual connect()
        this.logger.debug('Server-initiated disconnect - manual reconnect');
        try { this.socket?.connect(); } catch {}
        return;
      }
      // For other reasons (transport close, ping timeout), built-in reconnection will handle it
    });

    this.socket.on('connect_error', (error) => {
      // Only log connection errors if we're not already reconnecting
    if (this.connectionState !== SocketConnectionState.RECONNECTING) {
      this.logger.warn('Connect error', { metadata: { errorMessage: (error as Error).message || String(error) } });
      }
      this.handleConnectionError(error);
    });

    // Built-in reconnection lifecycle (no polling, websocket-only transport)
    this.socket.on('reconnect_attempt', (attempt) => {
      this.reconnectAttempts = attempt;
      this.updateConnectionState(SocketConnectionState.RECONNECTING);
      if (attempt <= 3 || attempt % 5 === 1) {
        this.logger.info('Reconnect attempt', { metadata: { attempt } });
      }
    });
    this.socket.on('reconnect', (attempt) => {
      this.logger.info('Reconnected', { metadata: { attempt } });
      this.reconnectionStrategy.reset();
      this.reconnectAttempts = 0;
      this.updateConnectionState(SocketConnectionState.CONNECTED);
      this.missedHeartbeats = 0;
      this.startHeartbeat();
    });
    this.socket.on('reconnect_error', (err) => {
      this.logger.warn('Reconnect error', { metadata: { errorMessage: (err as Error).message || String(err) } });
    });
    this.socket.on('reconnect_failed', () => {
      this.logger.warn('Reconnect failed - giving up');
      this.updateConnectionState(SocketConnectionState.DISCONNECTED);
    });

    // Set up custom event forwarding to event bus
    this.setupCustomEventForwarding();
  }

  private setupCustomEventForwarding(): void {
    if (!this.socket) return;

    // Forward all custom events to the event bus
    this.socket.onAny((event: string, ...args: unknown[]) => {
      // Skip built-in socket.io events
      const builtInEvents = [
        'connect', 'disconnect', 'connect_error', 'reconnect_attempt',
        'reconnect', 'reconnect_error', 'reconnect_failed',
        // Also skip app-internal heartbeat traffic so UI doesn't re-render
        'dashboard_heartbeat', 'dashboard_heartbeat_ack'
      ];
      if (!builtInEvents.includes(event)) {
        this.logger.debug('Forwarding event', { metadata: { event, payloadPreview: args[0] } });
        this.eventBus.publish(event, args[0]);
      }
    });
  }

  private handleConnectionError(error: Error): void {
    // Don't update state if we're already reconnecting
    if (this.connectionState !== SocketConnectionState.RECONNECTING) {
      this.updateConnectionState(SocketConnectionState.ERROR);
    }
    // Increment attempt counter (used by event handlers for visibility)
    this.reconnectAttempts++;

    // If strategy says no reconnect, move to disconnected
    if (!this.reconnectionStrategy.shouldReconnect(error)) {
      this.updateConnectionState(SocketConnectionState.DISCONNECTED);
    }
  }

  // ---------------- Heartbeat -----------------
  private startHeartbeat(): void {
    this.stopHeartbeat(); // ensure clean
    if (!this.socket) return;
    this.logger.debug('Starting heartbeat', { metadata: { intervalMs: this.heartbeatIntervalMs } });
    this.heartbeatTimer = setInterval(() => this.sendHeartbeat(), this.heartbeatIntervalMs);
    // Immediately send first heartbeat for faster detection
    this.sendHeartbeat();
    // Listen for ack
    const ackHandler = (payload: { ts: number }) => {
      if (payload?.ts) {
        const timeoutHandle = this.heartbeatAckTimeouts.get(payload.ts);
        if (timeoutHandle) {
          clearTimeout(timeoutHandle);
          this.heartbeatAckTimeouts.delete(payload.ts);
        }
        this.missedHeartbeats = 0; // reset miss counter
      }
    };
    // ensure no duplicate handlers
    if (this.onHeartbeatAckBound) {
      this.socket.off('dashboard_heartbeat_ack', this.onHeartbeatAckBound);
    }
    this.onHeartbeatAckBound = ackHandler;
    this.socket.on('dashboard_heartbeat_ack', this.onHeartbeatAckBound);
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = undefined;
    }
    if (this.socket && this.onHeartbeatAckBound) {
      this.socket.off('dashboard_heartbeat_ack', this.onHeartbeatAckBound);
      this.onHeartbeatAckBound = undefined;
    }
    // Clear pending ack timeouts
    for (const handle of this.heartbeatAckTimeouts.values()) {
      clearTimeout(handle);
    }
    this.heartbeatAckTimeouts.clear();
  }

  private sendHeartbeat(): void {
    if (!this.socket || !this.socket.connected) return;
    const ts = Date.now();
    try {
      this.socket.emit('dashboard_heartbeat', { ts });
      // Set an ack timeout for this heartbeat
      const ackTimeout = setTimeout(() => {
        this.heartbeatAckTimeouts.delete(ts);
        this.missedHeartbeats++;
        this.logger.warn('Heartbeat ack missed', { metadata: { ts, missedHeartbeats: this.missedHeartbeats } });
        if (this.missedHeartbeats >= this.maxMissedHeartbeats) {
          this.logger.warn('Heartbeat threshold exceeded - forcing reconnect');
          this.forceReconnect();
        }
      }, Math.min(this.heartbeatIntervalMs - 100, 4000));
      this.heartbeatAckTimeouts.set(ts, ackTimeout);
    } catch (err) {
      this.logger.error('Heartbeat emit failed', err as Error);
    }
  }

  private forceReconnect(): void {
    if (!this.socket) return;
    this.stopHeartbeat();
    this.logger.warn('Forcing reconnect due to missed heartbeats');
    try {
      this.socket.disconnect();
      this.socket.connect(); // Built-in reconnection will handle retry cadence
    } catch (err) {
      this.logger.error('Error during force reconnect', err as Error);
    }
    this.updateConnectionState(SocketConnectionState.RECONNECTING);
    this.missedHeartbeats = 0;
  }
}
