/**
 * Health routes - defines health check endpoints
 */

export default {
  routes: [
    {
      method: 'GET',
      path: '/health',
      handler: 'health.index',
      config: {
        auth: false, // No authentication required for health check
      },
    },
  ],
};