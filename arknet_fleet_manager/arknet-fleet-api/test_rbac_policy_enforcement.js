// RBAC Policy Enforcement Tests for Strapi Access Tiers
// Task 4419: Test policy enforcement for all tiers

const axios = require('axios');
const jwt = require('jsonwebtoken');

const BASE_URL = process.env.STRAPI_BASE_URL || 'http://localhost:1337';
const USERS = [
  { username: 'guest', password: 'guestpass', expectedTier: 'Guest', allowedRoutes: ['/public'], forbiddenRoutes: ['/dispatcher', '/admin'] },
  { username: 'dispatcher', password: 'dispatcherpass', expectedTier: 'Dispatcher', allowedRoutes: ['/dispatcher'], forbiddenRoutes: ['/admin'] },
  { username: 'admin', password: 'adminpass', expectedTier: 'Admin', allowedRoutes: ['/admin'], forbiddenRoutes: [] }
];

describe('RBAC Policy Enforcement', () => {
  USERS.forEach(user => {
    let token;
    it(`should login as ${user.username} and receive correct tier in JWT`, async () => {
      const res = await axios.post(`${BASE_URL}/api/auth/local`, {
        identifier: user.username,
        password: user.password
      });
      expect(res.data.jwt).toBeDefined();
      const decoded = jwt.decode(res.data.jwt);
      expect(decoded.tier).toBe(user.expectedTier);
      token = res.data.jwt;
    });

    user.allowedRoutes.forEach(route => {
      it(`${user.username} should access allowed route ${route}`, async () => {
        const res = await axios.get(`${BASE_URL}${route}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        expect(res.status).toBe(200);
      });
    });

    user.forbiddenRoutes.forEach(route => {
      it(`${user.username} should be forbidden from route ${route}`, async () => {
        try {
          await axios.get(`${BASE_URL}${route}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          throw new Error('Should not access forbidden route');
        } catch (err) {
          expect(err.response.status).toBe(403);
        }
      });
    });
  });
});
