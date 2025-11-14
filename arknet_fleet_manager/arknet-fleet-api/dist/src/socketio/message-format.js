"use strict";
/**
 * Socket.IO Message Format Standards
 *
 * Standardized message structures for all Socket.IO communication
 * in the ArkNet Transit System.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.validateMessage = exports.createMessage = exports.EventTypes = void 0;
/**
 * Event type constants
 */
exports.EventTypes = {
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
};
/**
 * Create a standardized Socket.IO message
 */
function createMessage(type, data, source, target, correlationId) {
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
exports.createMessage = createMessage;
/**
 * Generate a unique message ID
 */
function generateMessageId() {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
/**
 * Validate message structure
 */
function validateMessage(message) {
    return (typeof message === 'object' &&
        typeof message.id === 'string' &&
        typeof message.type === 'string' &&
        typeof message.timestamp === 'string' &&
        typeof message.source === 'string' &&
        message.data !== undefined);
}
exports.validateMessage = validateMessage;
//# sourceMappingURL=message-format.js.map