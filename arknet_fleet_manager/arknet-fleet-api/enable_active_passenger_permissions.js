/**
 * Enable public access to active-passenger API endpoints
 * Run with: node enable_active_passenger_permissions.js
 */

const fs = require('fs');
const path = require('path');

const permissionsFile = path.join(__dirname, 'src', 'extensions', 'users-permissions', 'config', 'permissions.json');

// Ensure directory exists
const permissionsDir = path.dirname(permissionsFile);
if (!fs.existsSync(permissionsDir)) {
  fs.mkdirSync(permissionsDir, { recursive: true });
}

// Define permissions
const permissions = {
  "active-passenger": {
    "controllers": {
      "active-passenger": {
        "find": {
          "enabled": true,
          "policy": ""
        },
        "findOne": {
          "enabled": true,
          "policy": ""
        },
        "create": {
          "enabled": true,
          "policy": ""
        },
        "update": {
          "enabled": true,
          "policy": ""
        },
        "delete": {
          "enabled": true,
          "policy": ""
        },
        "markBoarded": {
          "enabled": true,
          "policy": ""
        },
        "markAlighted": {
          "enabled": true,
          "policy": ""
        },
        "findNearLocation": {
          "enabled": true,
          "policy": ""
        },
        "findByRoute": {
          "enabled": true,
          "policy": ""
        },
        "findByStatus": {
          "enabled": true,
          "policy": ""
        },
        "deleteExpired": {
          "enabled": true,
          "policy": ""
        },
        "getCount": {
          "enabled": true,
          "policy": ""
        }
      }
    }
  }
};

// Write permissions file
fs.writeFileSync(permissionsFile, JSON.stringify(permissions, null, 2));

console.log('✅ Permissions file created at:', permissionsFile);
console.log('📋 Enabled endpoints:');
console.log('  - GET    /api/active-passengers');
console.log('  - GET    /api/active-passengers/:id');
console.log('  - POST   /api/active-passengers');
console.log('  - PUT    /api/active-passengers/:id');
console.log('  - DELETE /api/active-passengers/:id');
console.log('  - POST   /api/active-passengers/mark-boarded/:id');
console.log('  - POST   /api/active-passengers/mark-alighted/:id');
console.log('  - GET    /api/active-passengers/near-location');
console.log('  - GET    /api/active-passengers/by-route/:routeId');
console.log('  - GET    /api/active-passengers/by-status/:status');
console.log('  - DELETE /api/active-passengers/cleanup/expired');
console.log('  - GET    /api/active-passengers/stats/count');
console.log('\n⚠️  Note: Restart Strapi for changes to take effect');
