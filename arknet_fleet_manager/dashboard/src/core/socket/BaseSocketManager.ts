// Base Socket.IO Manager following SOLID principles
import { io, Socket } from 'socket.io-client';
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

  constructor(
    protected config: ISocketConfig,
    protected reconnectionStrategy: ISocketReconnectionStrategy = new ExponentialBackoffReconnectionStrategy()
  ) {}

  async connect(): Promise<void> {
    if (this.socket?.connected) {
      console.log('[BaseSocketManager] Already connected');
      return;
    }

    console.log('[BaseSocketManager] Connecting to', this.config.url);
    this.updateConnectionState(SocketConnectionState.CONNECTING);

    try {
      this.socket = io(this.config.url, this.config.options);

      this.setupSocketEventHandlers();
      this.setupCustomEventHandlers();

      return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
          console.error('[BaseSocketManager] Connection timeout after', this.config.options?.timeout || 10000, 'ms');
          this.updateConnectionState(SocketConnectionState.DISCONNECTED);
          reject(new Error('Connection timeout'));
        }, this.config.options?.timeout || 10000);

        this.socket!.once('connect', () => {
          console.log('[BaseSocketManager] Successfully connected!');
          clearTimeout(timeout);
          this.reconnectionStrategy.reset();
          this.reconnectAttempts = 0;
          this.updateConnectionState(SocketConnectionState.CONNECTED);
          resolve();
        });

        this.socket!.once('connect_error', (error) => {
          console.warn('[BaseSocketManager] Connection error:', error.message || error);
          clearTimeout(timeout);
          this.handleConnectionError(error);
          // If connection fails, set state to DISCONNECTED
          this.updateConnectionState(SocketConnectionState.DISCONNECTED);
          reject(error);
        });

        // Manually trigger connection if autoConnect is false
        if (this.config.options?.autoConnect === false) {
          console.log('[BaseSocketManager] Manually triggering connection (autoConnect=false)');
          this.socket!.connect();
        }
      });
    } catch (error) {
      console.error('[BaseSocketManager] Exception during connect:', error);
      this.handleConnectionError(error as Error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.updateConnectionState(SocketConnectionState.DISCONNECTED);
    this.reconnectionStrategy.reset();
    this.reconnectAttempts = 0;
  }

  emit(event: string, data?: unknown): void {
    if (this.socket?.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('[BaseSocketManager] Cannot emit event: socket not connected', event);
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
      console.log('[BaseSocketManager] Connected to server');
      this.reconnectionStrategy.reset();
      this.reconnectAttempts = 0;
      this.updateConnectionState(SocketConnectionState.CONNECTED);
    });

    this.socket.on('disconnect', (reason) => {
      console.log('[BaseSocketManager] Disconnected:', reason);
      this.updateConnectionState(SocketConnectionState.DISCONNECTED);

      if (reason === 'io server disconnect' || reason === 'io client disconnect') {
        // Don't auto-reconnect for intentional disconnects
        return;
      }

      this.attemptReconnection();
    });

    this.socket.on('connect_error', (error) => {
      console.warn('[BaseSocketManager] Connection error (will retry):', error.message || error);
      this.handleConnectionError(error);
    });

    this.socket.on('reconnect_attempt', (attempt) => {
      console.log(`[BaseSocketManager] Reconnection attempt ${attempt}`);
      this.reconnectAttempts = attempt;
      this.updateConnectionState(SocketConnectionState.RECONNECTING);
    });

    this.socket.on('reconnect', (attempt) => {
      console.log(`[BaseSocketManager] Reconnected after ${attempt} attempts`);
      this.reconnectAttempts = 0;
      this.updateConnectionState(SocketConnectionState.CONNECTED);
    });

    this.socket.on('reconnect_error', (error) => {
      console.warn('[BaseSocketManager] Reconnection error:', error.message || error);
      this.handleConnectionError(error);
    });

    this.socket.on('reconnect_failed', () => {
      console.log('[BaseSocketManager] Reconnection failed');
      this.updateConnectionState(SocketConnectionState.ERROR);
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
        'reconnect', 'reconnect_error', 'reconnect_failed'
      ];
      if (!builtInEvents.includes(event)) {
        try {
          console.debug('[BaseSocketManager] Forwarding event', event, args[0]);
        } catch {}
        this.eventBus.publish(event, args[0]);
      }
    });
  }

  private handleConnectionError(error: Error): void {
    this.updateConnectionState(SocketConnectionState.ERROR);

    if (this.reconnectionStrategy.shouldReconnect(error)) {
      this.attemptReconnection();
    } else {
      // If not reconnecting, set state to DISCONNECTED
      this.updateConnectionState(SocketConnectionState.DISCONNECTED);
    }
  }

  private attemptReconnection(): void {
    const delay = this.reconnectionStrategy.getReconnectDelay(this.reconnectAttempts);

    if (delay > 0) {
      setTimeout(() => {
        if (this.connectionState !== SocketConnectionState.CONNECTED) {
          console.log(`[BaseSocketManager] Attempting reconnection in ${delay}ms`);
          this.connect().catch(err => {
            console.error('[BaseSocketManager] Reconnection failed:', err);
            // If reconnection fails, set state to DISCONNECTED
            this.updateConnectionState(SocketConnectionState.DISCONNECTED);
          });
        }
      }, delay);
    } else {
      console.log('[BaseSocketManager] Max reconnection attempts reached');
      this.updateConnectionState(SocketConnectionState.DISCONNECTED);
    }
  }
}