// Socket.IO components following SOLID principles - Main exports
export { BaseSocketManager, ExponentialBackoffReconnectionStrategy } from './BaseSocketManager';
export { ServiceSocketManager } from './ServiceSocketManager';
export { SocketEventBus, BaseSocketEventHandler, FilteredSocketEventHandler, SocketEventFilters } from './SocketEventBus';

// Re-export interfaces for convenience
export type {
  ISocketConnectionManager,
  ISocketEventHandler,
  ISocketEventSubscriber,
  ISocketEventFilter,
  ISocketEventBus,
  ISocketReconnectionStrategy,
  ISocketConfig,
  SocketConnectionState,
  SocketConnectionStatus
} from '../../interfaces/socket';