/**
 * Passenger Spawning API Routes - TypeScript
 */

export default {
  routes: [
    {
      method: 'POST',
      path: '/passenger-spawning/generate',
      handler: 'passenger-spawning.generate',
      config: {
        policies: [],
        middlewares: [],
      },
    },
  ],
};