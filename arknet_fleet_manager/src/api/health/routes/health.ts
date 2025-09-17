export default {
  routes: [
    {
      method: 'GET',
      path: '/health',
      handler: async (ctx) => {
        ctx.body = { status: 'ok', timestamp: new Date().toISOString() };
      },
      config: {
        auth: false,
      },
    },
  ],
};