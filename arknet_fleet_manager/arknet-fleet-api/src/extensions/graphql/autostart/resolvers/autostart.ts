import type { Core } from '@strapi/strapi';

// Helper to extract user ID from JWT token in Authorization header
const getUserIdFromContext = async (ctx: any, strapi: Core.Strapi): Promise<number | null> => {
  try {
    // Access the Koa context - in Strapi GraphQL, it's nested in the context object
    const koaCtx = ctx.koaContext || ctx.context || ctx;
    
    // Get authorization header - try multiple locations
    const authHeader = koaCtx?.request?.headers?.authorization || 
                       koaCtx?.request?.header?.authorization ||
                       koaCtx?.req?.headers?.authorization ||
                       koaCtx?.headers?.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return null;
    }

    const token = authHeader.substring(7);
    const jwtService = strapi.plugin('users-permissions').service('jwt');
    
    // Verify token - jwtService.verify returns a promise
    const decoded: any = await jwtService.verify(token);
    
    return decoded?.id || null;
  } catch (error) {
    strapi.log.warn('Failed to authenticate GraphQL request:', error);
    return null;
  }
};

// SCHEMA-FIRST: Plain resolver functions, not Nexus types
export default ({ strapi }: { strapi: Core.Strapi }) => ({
  Query: {
    myAutostartSettings: async (_root: any, _args: any, ctx: any) => {
      try {
        const userId = await getUserIdFromContext(ctx, strapi);
        if (!userId) {
          return { success: false, settings: [] };
        }
        const settings = await strapi.entityService.findMany('api::autostart.autostart-setting' as any, {
          filters: { user: userId },
          populate: ['user'],
        });
        return { success: true, settings };
      } catch (error) {
        strapi.log.error('Error fetching autostart settings:', error);
        return { success: false, settings: [] };
      }
    },
  },
  Mutation: {
    setAutostartSetting: async (_root: any, args: any, ctx: any) => {
      try {
        const userId = await getUserIdFromContext(ctx, strapi);
        if (!userId) {
          return { success: false, error: 'Authentication required' };
        }
        const { serviceId, serviceName, enabled, schedule } = args;
        const existing = await strapi.entityService.findMany('api::autostart.autostart-setting' as any, {
          filters: { user: userId, serviceId },
        });
        let setting;
        if (existing && existing.length > 0) {
          setting = await strapi.entityService.update('api::autostart.autostart-setting' as any, (existing as any[])[0].id, {
            data: { serviceName, enabled, schedule },
          });
        } else {
          setting = await strapi.entityService.create('api::autostart.autostart-setting' as any, {
            data: { user: userId, serviceId, serviceName, enabled, schedule },
          });
        }
        return { success: true, setting };
      } catch (error) {
        strapi.log.error('Error setting autostart setting:', error);
        return { success: false, error: (error as Error).message };
      }
    },
    removeAutostartSetting: async (_root: any, args: any, ctx: any) => {
      try {
        const userId = await getUserIdFromContext(ctx, strapi);
        if (!userId) {
          return { success: false, message: 'Authentication required' };
        }
        const { id } = args;
        const setting = await strapi.entityService.findOne('api::autostart.autostart-setting' as any, id, {
          populate: ['user'],
        });
        if (!setting || (setting as any).user.id !== userId) {
          return { success: false, message: 'Setting not found or access denied' };
        }
        await strapi.entityService.delete('api::autostart.autostart-setting' as any, id);
        return { success: true, message: 'Autostart setting removed successfully' };
      } catch (error) {
        strapi.log.error('Error removing autostart setting:', error);
        return { success: false, message: 'Failed to remove setting' };
      }
    },
  },
});

// Old Nexus code-first implementation removed below this line
