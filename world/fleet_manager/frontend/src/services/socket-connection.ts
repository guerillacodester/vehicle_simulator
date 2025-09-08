/**
 * REAL-TIME CONNECTION SERVICE
 * Uses Socket.io for instant connection status updates
 */

import { io, Socket } from 'socket.io-client';

interface ConnectionStatus {
  isConnected: boolean;
  responseTime?: number;
  error?: string;
  lastChecked?: Date;
}

type ConnectionStatusCallback = (status: ConnectionStatus) => void;

class SocketConnectionService {
  private socket: Socket | null = null;
  private callbacks: Set<ConnectionStatusCallback> = new Set();
  private currentStatus: ConnectionStatus = { isConnected: false };
  private pingStartTime: number = 0;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 10;

  constructor(private serverUrl: string = 'http://localhost:8000') {}

  /**
   * Initialize the socket connection
   */
  connect(): void {
    if (this.socket?.connected) {
      return; // Already connected
    }

    console.log('🔌 Initializing Socket.io connection to:', this.serverUrl);

    this.socket = io(this.serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 5000,
      forceNew: true,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: 1000,
      reconnectionDelayMax: 5000,
    });

    this.setupEventHandlers();
  }

  /**
   * Disconnect the socket
   */
  disconnect(): void {
    if (this.socket) {
      console.log('🔌 Disconnecting Socket.io connection');
      this.socket.disconnect();
      this.socket = null;
    }
  }

  /**
   * Subscribe to connection status changes
   */
  onStatusChange(callback: ConnectionStatusCallback): () => void {
    this.callbacks.add(callback);
    
    // Immediately call with current status
    callback(this.currentStatus);
    
    // Return unsubscribe function
    return () => {
      this.callbacks.delete(callback);
    };
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return { ...this.currentStatus };
  }

  /**
   * Send a ping to test connection latency
   */
  ping(): void {
    if (this.socket?.connected) {
      this.pingStartTime = Date.now();
      this.socket.emit('ping', { timestamp: this.pingStartTime });
    }
  }

  /**
   * Setup socket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('✅ Socket.io connected');
      this.reconnectAttempts = 0;
      this.updateStatus({
        isConnected: true,
        lastChecked: new Date(),
        error: undefined
      });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('❌ Socket.io disconnected:', reason);
      this.updateStatus({
        isConnected: false,
        lastChecked: new Date(),
        error: `Disconnected: ${reason}`
      });
    });

    this.socket.on('connect_error', (error) => {
      console.log('🚨 Socket.io connection error:', error.message);
      this.updateStatus({
        isConnected: false,
        lastChecked: new Date(),
        error: `Connection error: ${error.message}`
      });
    });

    this.socket.on('reconnect', (attemptNumber) => {
      console.log(`🔄 Socket.io reconnected after ${attemptNumber} attempts`);
      this.updateStatus({
        isConnected: true,
        lastChecked: new Date(),
        error: undefined
      });
    });

    this.socket.on('reconnect_attempt', (attemptNumber) => {
      console.log(`🔄 Socket.io reconnection attempt ${attemptNumber}`);
      this.reconnectAttempts = attemptNumber;
    });

    this.socket.on('reconnect_error', (error) => {
      console.log('🚨 Socket.io reconnection error:', error.message);
    });

    this.socket.on('reconnect_failed', () => {
      console.log('💀 Socket.io reconnection failed - giving up');
      this.updateStatus({
        isConnected: false,
        lastChecked: new Date(),
        error: 'Reconnection failed - server may be down'
      });
    });

    this.socket.on('pong', (data) => {
      if (data.timestamp === this.pingStartTime) {
        const responseTime = Date.now() - this.pingStartTime;
        console.log(`🏓 Ping response: ${responseTime}ms`);
        this.updateStatus({
          ...this.currentStatus,
          responseTime,
          lastChecked: new Date()
        });
      }
    });

    this.socket.on('connection_status', (data) => {
      console.log('📡 Server status update:', data);
    });
  }

  /**
   * Update connection status and notify all callbacks
   */
  private updateStatus(newStatus: Partial<ConnectionStatus>): void {
    this.currentStatus = { ...this.currentStatus, ...newStatus };
    
    // Notify all subscribers
    this.callbacks.forEach(callback => {
      try {
        callback(this.currentStatus);
      } catch (error) {
        console.error('Error in connection status callback:', error);
      }
    });
  }
}

// Export singleton instance
export const socketConnectionService = new SocketConnectionService();
export type { ConnectionStatus };
