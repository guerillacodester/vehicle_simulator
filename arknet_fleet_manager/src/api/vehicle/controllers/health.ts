/**
 * Health controller - provides health check endpoint for simulator
 */

export default {
  async index(ctx) {
    ctx.body = {
      status: 'ok',
      service: 'arknet-fleet-manager',
      timestamp: new Date().toISOString(),
      database: 'connected'
    };
  },
};