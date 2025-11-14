/**
 * Common types for Socket.IO communication
 */

export enum CommuterDirection {
  INBOUND = 'inbound',
  OUTBOUND = 'outbound',
}

export enum ReservoirType {
  DEPOT = 'depot',
  ROUTE = 'route',
}

export enum ServiceType {
  COMMUTER_SERVICE = 'commuter-service',
  VEHICLE_CONDUCTOR = 'vehicle-conductor',
  DEPOT_MANAGER = 'depot-manager',
  SIMULATOR = 'simulator',
}
