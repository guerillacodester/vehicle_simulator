/**
 * Socket.IO Message Format Standards
 * 
 * Standardized message structures for all Socket.IO communication
 * in the ArkNet Transit System.
 */

import { CommuterDirection, ReservoirType } from './types';

/**
 * Base message structure for all Socket.IO events
 */
export interface SocketIOMessage<T = any> {
  /** Unique message identifier */
  id: string;
  
  /** Message type (event name) */
  type: string;
  
  /** ISO 8601 timestamp */
  timestamp: string;
  
  /** Source service identifier */
  source: string;
  
  /** Target service(s) - null for broadcast */
  target?: string | string[] | null;
  
  /** Message payload */
  data: T;
  
  /** Optional correlation ID for request-response tracking */
  correlationId?: string;
  
  /** Optional metadata */
  metadata?: Record<string, any>;
}

/**
 * Commuter data structure
 */
export interface CommuterData {
  /** Unique commuter identifier */
  commuter_id: string;
  
  /** Commuter's current GPS location */
  current_location: {
    lat: number;
    lon: number;
  };
  
  /** Destination GPS location */
  destination: {
    lat: number;
    lon: number;
  };
  
  /** Travel direction */
  direction: CommuterDirection;
  
  /** Priority level (1=highest, 5=lowest) */
  priority: number;
  
  /** Maximum walking distance (meters) */
  max_walking_distance: number;
  
  /** Spawn timestamp */
  spawn_time: string;
  
  /** Optional bus stop association */
  nearest_bus_stop?: {
    stop_id: string;
    name: string;
    distance_meters: number;
  };
}

/**
 * Vehicle query request
 */
export interface VehicleQueryRequest {
  /** Vehicle identifier */
  vehicle_id: string;
  
  /** Route identifier */
  route_id: string;
  
  /** Current vehicle location */
  vehicle_location: {
    lat: number;
    lon: number;
  };
  
  /** Search radius (meters) */
  search_radius: number;
  
  /** Available seats */
  available_seats: number;
  
  /** Travel direction */
  direction: CommuterDirection;
  
  /** Reservoir type to query */
  reservoir_type: ReservoirType;
}

/**
 * Commuter match response
 */
export interface CommuterMatchResponse {
  /** List of matching commuters */
  commuters: CommuterData[];
  
  /** Total count of matches */
  total_count: number;
  
  /** Query execution time (milliseconds) */
  query_time_ms: number;
  
  /** Reservoir queried */
  reservoir_type: ReservoirType;
}

/**
 * Depot queue status
 */
export interface DepotQueueStatus {
  /** Depot identifier */
  depot_id: string;
  
  /** Route identifier */
  route_id: string;
  
  /** Queue length */
  queue_length: number;
  
  /** Current head vehicle */
  head_vehicle?: {
    vehicle_id: string;
    seats_filled: number;
    total_seats: number;
    waiting_since: string;
  };
  
  /** Total commuters waiting */
  waiting_commuters: number;
}

/**
 * Vehicle departure notification
 */
export interface VehicleDepartureEvent {
  /** Vehicle identifier */
  vehicle_id: string;
  
  /** Route identifier */
  route_id: string;
  
  /** Depot identifier */
  depot_id: string;
  
  /** Departure timestamp */
  departure_time: string;
  
  /** Passenger count */
  passenger_count: number;
  
  /** Next vehicle in queue (if any) */
  next_vehicle_id?: string;
}

/**
 * System health status
 */
export interface SystemHealthStatus {
  /** Service name */
  service: string;
  
  /** Status */
  status: 'healthy' | 'degraded' | 'unhealthy';
  
  /** Uptime (seconds) */
  uptime_seconds: number;
  
  /** Active connections */
  active_connections: number;
  
  /** Messages processed (last minute) */
  messages_per_minute: number;
  
  /** Last check timestamp */
  last_check: string;
}

/**
 * Driver location update (broadcast from vehicle driver)
 */
export interface DriverLocationUpdate {
  /** Vehicle identifier */
  vehicle_id: string;
  
  /** Driver identifier */
  driver_id: string;
  
  /** Current latitude */
  latitude: number;
  
  /** Current longitude */
  longitude: number;
  
  /** Current speed (km/h) */
  speed: number;
  
  /** Current heading (degrees, 0-360) */
  heading: number;
  
  /** Timestamp of location update */
  timestamp: string;
}

/**
 * Conductor stop request (from conductor to driver)
 */
export interface ConductorStopRequest {
  /** Vehicle identifier */
  vehicle_id: string;
  
  /** Conductor identifier */
  conductor_id: string;
  
  /** Stop identifier */
  stop_id: string;
  
  /** Number of passengers boarding */
  passengers_boarding: number;
  
  /** Number of passengers disembarking */
  passengers_disembarking: number;
  
  /** Requested stop duration (seconds) */
  duration_seconds: number;
  
  /** GPS position of stop [lat, lon] */
  gps_position: [number, number];
}

/**
 * Conductor ready to depart (from conductor to driver)
 */
export interface ConductorReadyToDepart {
  /** Vehicle identifier */
  vehicle_id: string;
  
  /** Conductor identifier */
  conductor_id: string;
  
  /** Current passenger count on board */
  passenger_count: number;
  
  /** Timestamp of ready signal */
  timestamp: string;
}

/**
 * Conductor query passengers request
 */
export interface ConductorQueryPassengers {
  /** Depot identifier */
  depot_id: string;
  
  /** Route identifier */
  route_id: string;
  
  /** Current vehicle position [lat, lon] */
  current_position: [number, number];
}

/**
 * Passenger query response (to conductor)
 */
export interface PassengerQueryResponse {
  /** List of eligible passengers */
  passengers: Array<{
    /** Passenger identifier */
    passenger_id: string;
    
    /** Pickup latitude */
    pickup_lat: number;
    
    /** Pickup longitude */
    pickup_lon: number;
    
    /** Dropoff latitude */
    dropoff_lat: number;
    
    /** Dropoff longitude */
    dropoff_lon: number;
    
    /** Time window start (ISO 8601) */
    time_window_start: string;
    
    /** Time window end (ISO 8601) */
    time_window_end: string;
  }>;
}

/**
 * Passenger lifecycle event (board, alight, waiting, cancelled)
 */
export interface PassengerLifecycleEvent {
  /** Passenger identifier */
  passenger_id: string;
  
  /** Event type */
  event_type: 'board' | 'alight' | 'waiting' | 'cancelled';
  
  /** Vehicle identifier (optional, for board/alight) */
  vehicle_id?: string;
  
  /** Location of event [lat, lon] */
  location: [number, number];
  
  /** Timestamp of event */
  timestamp: string;
}

/**
 * Event type constants
 */
export const EventTypes = {
  // Commuter Service Events
  COMMUTER_SPAWNED: 'commuter:spawned',
  COMMUTER_PICKED_UP: 'commuter:picked_up',
  COMMUTER_DROPPED_OFF: 'commuter:dropped_off',
  COMMUTER_EXPIRED: 'commuter:expired',
  
  // Vehicle Query Events
  QUERY_COMMUTERS: 'vehicle:query_commuters',
  COMMUTERS_FOUND: 'vehicle:commuters_found',
  NO_COMMUTERS_FOUND: 'vehicle:no_commuters',
  
  // Depot Queue Events
  DEPOT_QUEUE_JOIN: 'depot:queue_join',
  DEPOT_QUEUE_UPDATE: 'depot:queue_update',
  DEPOT_VEHICLE_DEPART: 'depot:vehicle_depart',
  DEPOT_SEATS_FILLED: 'depot:seats_filled',
  
  // Driver Events (Priority 2)
  DRIVER_LOCATION_UPDATE: 'driver:location:update',
  
  // Conductor Events (Priority 2)
  CONDUCTOR_REQUEST_STOP: 'conductor:request:stop',
  CONDUCTOR_READY_DEPART: 'conductor:ready:depart',
  CONDUCTOR_QUERY_PASSENGERS: 'conductor:query:passengers',
  
  // Passenger Events (Priority 2)
  PASSENGER_LIFECYCLE_EVENT: 'passenger:lifecycle',
  PASSENGER_BOARD_VEHICLE: 'passenger:board:vehicle',
  PASSENGER_ALIGHT_VEHICLE: 'passenger:alight:vehicle',
  
  // System Events
  SERVICE_CONNECTED: 'system:service_connected',
  SERVICE_DISCONNECTED: 'system:service_disconnected',
  HEALTH_CHECK: 'system:health_check',
  ERROR: 'system:error',
} as const;

/**
 * Create a standardized Socket.IO message
 */
export function createMessage<T>(
  type: string,
  data: T,
  source: string,
  target?: string | string[] | null,
  correlationId?: string
): SocketIOMessage<T> {
  return {
    id: generateMessageId(),
    type,
    timestamp: new Date().toISOString(),
    source,
    target,
    data,
    correlationId,
  };
}

/**
 * Generate a unique message ID
 */
function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Validate message structure
 */
export function validateMessage(message: any): message is SocketIOMessage {
  return (
    typeof message === 'object' &&
    typeof message.id === 'string' &&
    typeof message.type === 'string' &&
    typeof message.timestamp === 'string' &&
    typeof message.source === 'string' &&
    message.data !== undefined
  );
}
