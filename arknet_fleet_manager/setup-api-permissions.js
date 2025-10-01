/**
 * Setup API permissions for public access to enable simulator access
 */

const strapi = require('@strapi/strapi');

async function setupPermissions() {
  const app = await strapi().load();
  
  try {
    // Get the public role
    const publicRole = await app.entityService.findMany('plugin::users-permissions.role', {
      filters: { type: 'public' }
    });
    
    if (!publicRole || publicRole.length === 0) {
      console.error('Public role not found');
      return;
    }
    
    const publicRoleId = publicRole[0].id;
    console.log('Found public role ID:', publicRoleId);
    
    // Define the permissions we need for the simulator
    const permissions = [
      // Vehicle permissions
      { action: 'find', subject: 'api::vehicle.vehicle' },
      { action: 'findOne', subject: 'api::vehicle.vehicle' },
      
      // Driver permissions
      { action: 'find', subject: 'api::driver.driver' },
      { action: 'findOne', subject: 'api::driver.driver' },
      
      // Route permissions
      { action: 'find', subject: 'api::route.route' },
      { action: 'findOne', subject: 'api::route.route' },
      
      // Depot permissions
      { action: 'find', subject: 'api::depot.depot' },
      { action: 'findOne', subject: 'api::depot.depot' },
    ];
    
    // Update or create permissions
    for (const permission of permissions) {
      try {
        // Check if permission already exists
        const existingPermissions = await app.entityService.findMany('plugin::users-permissions.permission', {
          filters: {
            role: publicRoleId,
            action: permission.action,
            subject: permission.subject
          }
        });
        
        if (existingPermissions && existingPermissions.length === 0) {
          // Create new permission
          await app.entityService.create('plugin::users-permissions.permission', {
            data: {
              action: permission.action,
              subject: permission.subject,
              role: publicRoleId,
              enabled: true
            }
          });
          console.log(`✅ Created permission: ${permission.action} on ${permission.subject}`);
        } else {
          // Update existing permission to be enabled
          await app.entityService.update('plugin::users-permissions.permission', existingPermissions[0].id, {
            data: { enabled: true }
          });
          console.log(`✅ Updated permission: ${permission.action} on ${permission.subject}`);
        }
      } catch (error) {
        console.error(`❌ Error setting permission ${permission.action} on ${permission.subject}:`, error.message);
      }
    }
    
    console.log('\n🎉 API permissions setup complete!');
    console.log('The simulator should now be able to access Strapi APIs.');
    
  } catch (error) {
    console.error('❌ Error during setup:', error);
  } finally {
    await app.destroy();
  }
}

if (require.main === module) {
  setupPermissions().catch(console.error);
}

module.exports = setupPermissions;