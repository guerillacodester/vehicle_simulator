"use strict";
/**
 * Vehicle Event Controller
 * =========================
 *
 * Handles hardware-triggered events from real-world vehicle devices:
 * - GPS position updates
 * - Door sensor events
 * - RFID card taps
 * - Passenger counters
 * - Driver confirmations
 * - Stop arrival/departure detection
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = {
    /**
     * GPS Position Update
     * Hardware: GPS tracker sends position every 5-30 seconds
     */
    async updatePosition(ctx) {
        try {
            const { vehicle_id, latitude, longitude, speed, heading, timestamp } = ctx.request.body;
            // Validate required fields
            if (!vehicle_id || latitude === undefined || longitude === undefined) {
                return ctx.badRequest('Missing required fields: vehicle_id, latitude, longitude');
            }
            // Create vehicle event record
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'gps_position',
                    latitude,
                    longitude,
                    speed: speed || 0,
                    heading: heading || 0,
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            // Update vehicle status (if vehicle-status API exists)
            try {
                await strapi.entityService.update('api::vehicle-status.vehicle-status', vehicle_id, {
                    data: {
                        last_latitude: latitude,
                        last_longitude: longitude,
                        last_speed: speed || 0,
                        last_heading: heading || 0,
                        last_update: timestamp || new Date().toISOString(),
                    },
                });
            }
            catch (err) {
                // Vehicle status might not exist yet, log but don't fail
                strapi.log.debug(`Could not update vehicle status for ${vehicle_id}: ${err.message}`);
            }
            return ctx.send({
                success: true,
                event_id: event.id,
                message: 'Position updated',
            });
        }
        catch (error) {
            strapi.log.error('Error updating vehicle position:', error);
            return ctx.internalServerError('Failed to update position');
        }
    },
    /**
     * Door Sensor Event
     * Hardware: Magnetic door sensors detect door open/close
     */
    async doorEvent(ctx) {
        try {
            const { vehicle_id, door_state, timestamp } = ctx.request.body;
            if (!vehicle_id || !door_state) {
                return ctx.badRequest('Missing required fields: vehicle_id, door_state');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'door_event',
                    event_data: { door_state },
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `Door ${door_state}`,
            });
        }
        catch (error) {
            strapi.log.error('Error recording door event:', error);
            return ctx.internalServerError('Failed to record door event');
        }
    },
    /**
     * RFID Card Tap
     * Hardware: RFID reader detects passenger smart card
     */
    async rfidTap(ctx) {
        try {
            const { vehicle_id, card_id, tap_type, timestamp } = ctx.request.body;
            if (!vehicle_id || !card_id) {
                return ctx.badRequest('Missing required fields: vehicle_id, card_id');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'rfid_tap',
                    event_data: { card_id, tap_type },
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `RFID tap recorded for card ${card_id}`,
            });
        }
        catch (error) {
            strapi.log.error('Error recording RFID tap:', error);
            return ctx.internalServerError('Failed to record RFID tap');
        }
    },
    /**
     * Passenger Count Update
     * Hardware: IR sensors count passengers entering/exiting
     */
    async updatePassengerCount(ctx) {
        try {
            const { vehicle_id, passenger_count, timestamp } = ctx.request.body;
            if (!vehicle_id || passenger_count === undefined) {
                return ctx.badRequest('Missing required fields: vehicle_id, passenger_count');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'passenger_count',
                    event_data: { passenger_count },
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `Passenger count updated: ${passenger_count}`,
            });
        }
        catch (error) {
            strapi.log.error('Error updating passenger count:', error);
            return ctx.internalServerError('Failed to update passenger count');
        }
    },
    /**
     * Driver Confirm Boarding
     * Hardware: Driver tablet button press
     */
    async driverConfirmBoarding(ctx) {
        try {
            const { vehicle_id, passenger_id, stop_id, timestamp } = ctx.request.body;
            if (!vehicle_id || !passenger_id) {
                return ctx.badRequest('Missing required fields: vehicle_id, passenger_id');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'driver_confirm_boarding',
                    event_data: { passenger_id, stop_id },
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            // Update passenger status to 'onboard'
            try {
                await strapi.entityService.update('api::active-passenger.active-passenger', passenger_id, {
                    data: {
                        status: 'onboard',
                        boarding_time: timestamp || new Date().toISOString(),
                    },
                });
            }
            catch (err) {
                strapi.log.warn(`Could not update passenger ${passenger_id} status: ${err.message}`);
            }
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `Boarding confirmed for passenger ${passenger_id}`,
            });
        }
        catch (error) {
            strapi.log.error('Error confirming boarding:', error);
            return ctx.internalServerError('Failed to confirm boarding');
        }
    },
    /**
     * Driver Confirm Alighting
     * Hardware: Driver tablet button press
     */
    async driverConfirmAlighting(ctx) {
        try {
            const { vehicle_id, passenger_id, stop_id, timestamp } = ctx.request.body;
            if (!vehicle_id || !passenger_id) {
                return ctx.badRequest('Missing required fields: vehicle_id, passenger_id');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'driver_confirm_alighting',
                    event_data: { passenger_id, stop_id },
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            // Update passenger status to 'completed'
            try {
                await strapi.entityService.update('api::active-passenger.active-passenger', passenger_id, {
                    data: {
                        status: 'completed',
                        alighting_time: timestamp || new Date().toISOString(),
                    },
                });
            }
            catch (err) {
                strapi.log.warn(`Could not update passenger ${passenger_id} status: ${err.message}`);
            }
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `Alighting confirmed for passenger ${passenger_id}`,
            });
        }
        catch (error) {
            strapi.log.error('Error confirming alighting:', error);
            return ctx.internalServerError('Failed to confirm alighting');
        }
    },
    /**
     * Arrive at Stop
     * Hardware: Geofence trigger or driver button
     */
    async arriveAtStop(ctx) {
        try {
            const { vehicle_id, stop_id, latitude, longitude, timestamp } = ctx.request.body;
            if (!vehicle_id || !stop_id) {
                return ctx.badRequest('Missing required fields: vehicle_id, stop_id');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'arrive_stop',
                    event_data: { stop_id },
                    latitude,
                    longitude,
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `Arrival at stop ${stop_id} recorded`,
            });
        }
        catch (error) {
            strapi.log.error('Error recording stop arrival:', error);
            return ctx.internalServerError('Failed to record stop arrival');
        }
    },
    /**
     * Depart from Stop
     * Hardware: Geofence trigger or driver button
     */
    async departFromStop(ctx) {
        try {
            const { vehicle_id, stop_id, latitude, longitude, timestamp } = ctx.request.body;
            if (!vehicle_id || !stop_id) {
                return ctx.badRequest('Missing required fields: vehicle_id, stop_id');
            }
            const event = await strapi.entityService.create('api::vehicle-event.vehicle-event', {
                data: {
                    vehicle_id,
                    event_type: 'depart_stop',
                    event_data: { stop_id },
                    latitude,
                    longitude,
                    timestamp: timestamp || new Date().toISOString(),
                    publishedAt: new Date(),
                },
            });
            return ctx.send({
                success: true,
                event_id: event.id,
                message: `Departure from stop ${stop_id} recorded`,
            });
        }
        catch (error) {
            strapi.log.error('Error recording stop departure:', error);
            return ctx.internalServerError('Failed to record stop departure');
        }
    },
};
//# sourceMappingURL=vehicle-event.js.map