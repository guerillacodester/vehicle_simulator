/**
 * Vehicle Event API Routes
 * Hardware-triggered events for real-world vehicle tracking
 * 
 * These endpoints are called by physical hardware devices:
 * - GPS trackers
 * - Door sensors  
 * - RFID readers
 * - Driver tablets
 */

export default {
  routes: [
    // Hardware GPS position update
    {
      method: 'POST',
      path: '/vehicle-events/position',
      handler: 'vehicle-event.updatePosition',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Door sensor events
    {
      method: 'POST',
      path: '/vehicle-events/door',
      handler: 'vehicle-event.doorEvent',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // RFID card tap (passenger boarding)
    {
      method: 'POST',
      path: '/vehicle-events/rfid-tap',
      handler: 'vehicle-event.rfidTap',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Passenger counter update (IR sensor)
    {
      method: 'POST',
      path: '/vehicle-events/passenger-count',
      handler: 'vehicle-event.updatePassengerCount',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Driver manual confirmation (tablet)
    {
      method: 'POST',
      path: '/vehicle-events/driver-confirm-boarding',
      handler: 'vehicle-event.driverConfirmBoarding',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Driver manual confirmation (alighting)
    {
      method: 'POST',
      path: '/vehicle-events/driver-confirm-alighting',
      handler: 'vehicle-event.driverConfirmAlighting',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Automatic stop arrival detection
    {
      method: 'POST',
      path: '/vehicle-events/arrive-stop',
      handler: 'vehicle-event.arriveAtStop',
      config: {
        policies: [],
        middlewares: [],
      },
    },

    // Automatic stop departure detection
    {
      method: 'POST',
      path: '/vehicle-events/depart-stop',
      handler: 'vehicle-event.departFromStop',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};
