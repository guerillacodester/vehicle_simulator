// Socket.IO interfaces and types following SOLID principles

export enum SocketConnectionState {
  CONNECTING = 'connecting',
  CONNECTED = 'connected',
  DISCONNECTED = 'disconnected',
  ERROR = 'error',
  RECONNECTING = 'reconnecting'
}

export interface SocketConnectionStatus {
  state: SocketConnectionState;
  message: string;
  lastConnected?: Date;
  reconnectAttempts?: number;
}

export interface ISocketEventHandler<T = unknown> {
  handle(event: string, data: T): void;
  canHandle(event: string, data: T): boolean;
}

export interface ISocketEventSubscriber<T = unknown> {
  subscribe(event: string, handler: ISocketEventHandler<T>): void;
  unsubscribe(event: string, handler?: ISocketEventHandler<T>): void;
  getSubscriptions(): Map<string, ISocketEventHandler<T>[]>;
}

export interface ISocketEventFilter<T = unknown> {
  matches(event: string, data: T): boolean;
}

export interface ISocketEventBus<T = unknown> {
  publish(event: string, data: T): void;
  subscribe(event: string, handler: ISocketEventHandler<T>): () => void;
  unsubscribe(event: string, handler?: ISocketEventHandler<T>): void;
  clear(): void;
}

export interface ISocketConnectionManager {
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  emit(event: string, data?: unknown): void;
  on(event: string, handler: (data: unknown) => void): void;
  off(event: string, handler?: (data: unknown) => void): void;
  getConnectionStatus(): SocketConnectionStatus;
  onConnectionChange(handler: (status: SocketConnectionStatus) => void): void;
  offConnectionChange(handler: (status: SocketConnectionStatus) => void): void;
}

export interface ISocketEventEmitter {
  emit(event: string, data?: unknown): void;
}

export interface ISocketEventListener {
  on(event: string, handler: (data: unknown) => void): void;
  off(event: string, handler?: (data: unknown) => void): void;
}

export interface ISocketReconnectionStrategy {
  shouldReconnect(error: Error): boolean;
  getReconnectDelay(attempt: number): number;
  reset(): void;
}

export interface ISocketConfig {
  url: string;
  options?: {
    transports?: string[];
    timeout?: number;
    forceNew?: boolean;
    reconnection?: boolean;
    reconnectionAttempts?: number;
    reconnectionDelay?: number;
    autoConnect?: boolean;
    auth?: Record<string, string>;
    path?: string;
    extraHeaders?: Record<string, string>;
  };
}