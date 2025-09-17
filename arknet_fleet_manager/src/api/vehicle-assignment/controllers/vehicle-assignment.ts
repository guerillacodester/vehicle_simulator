import { factories } from '@strapi/strapi'

export default factories.createCoreController('api::vehicle-assignment.vehicle-assignment', ({ strapi }) => ({
  // Custom method for active assignments
  async active(ctx) {
    try {
      // For now, return mock data that matches what the simulator expects
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
    } catch (err) {
      ctx.throw(500, err);
    }
  },
}));
