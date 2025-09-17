export default (plugin) => {
  // Add legacy API routes for backwards compatibility with the simulator
  plugin.routes['content-api'].routes.push(
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
    {
      method: 'GET', 
      path: '/api/v1/vehicle-assignments/active',
      handler: async (ctx) => {
        // Mock data for simulator compatibility
        const mockAssignments = [
          {
            assignment_id: "1",
            driver_id: "d1",
            vehicle_id: "v1",
            route_id: "r1", 
            driver_name: "Test Driver",
            vehicle_reg_code: "TEST-001",
            route_name: "Test Route 1"
          }
        ];
        ctx.body = mockAssignments;
      },
      config: {
        auth: false,
      },
    },
    {
      method: 'GET',
      path: '/api/v1/routes/public/:routeCode/geometry',
      handler: async (ctx) => {
        // Mock geometry data
        const mockGeometry = {
          route_id: ctx.params.routeCode,
          route_name: `Route ${ctx.params.routeCode}`,
          geometry: {
            type: "LineString",
            coordinates: [
              [-59.6463, 13.2810],
              [-59.6464, 13.2811], 
              [-59.6465, 13.2812]
            ]
          },
          coordinate_count: 3
        };
        ctx.body = mockGeometry;
      },
      config: {
        auth: false,
      },
    }
  );

  return plugin;
};