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

export default ({ nexus, strapi }: { nexus: any; strapi: Core.Strapi }) => [
  // Define AutostartSettingsResponse type
  nexus.objectType({
    name: 'AutostartSettingsResponse',
    definition(t: any) {
      t.nonNull.boolean('success');
      t.nonNull.list.nonNull.field('settings', { type: 'AutostartSetting' });
    },
  }),

  // Define SetAutostartSettingResponse type
  nexus.objectType({
    name: 'SetAutostartSettingResponse',
    definition(t: any) {
      t.nonNull.boolean('success');
      t.field('setting', { type: 'AutostartSetting' });
      t.string('error');
    },
  }),

  // Define RemoveAutostartSettingResponse type
  nexus.objectType({
    name: 'RemoveAutostartSettingResponse',
    definition(t: any) {
      t.nonNull.boolean('success');
      t.nonNull.string('message');
    },
  }),

  // Extend Query type with autostartSettings field
  nexus.extendType({
    type: 'Query',
    definition(t: any) {
      t.nonNull.field('autostartSettings', {
        type: 'AutostartSettingsResponse',
        async resolve(_root: any, _args: any, ctx: any) {
          try {
            const userId = await getUserIdFromContext(ctx, strapi);
            if (!userId) {
              return {
                success: false,
                settings: [],
              };
            }

            const settings = await strapi.entityService.findMany('api::autostart.autostart-setting' as any, {
              filters: { user: userId },
              populate: ['user'],
            });

            return {
              success: true,
              settings,
            };
          } catch (error) {
            strapi.log.error('Error fetching autostart settings:', error);
            return {
              success: false,
              settings: [],
            };
          }
        },
      });
    },
  }),

  // Extend Mutation type with setAutostartSetting and removeAutostartSetting
  nexus.extendType({
    type: 'Mutation',
    definition(t: any) {
      t.nonNull.field('setAutostartSetting', {
        type: 'SetAutostartSettingResponse',
        args: {
          serviceId: nexus.nonNull(nexus.stringArg()),
          serviceName: nexus.nonNull(nexus.stringArg()),
          enabled: nexus.nonNull(nexus.booleanArg()),
          schedule: nexus.stringArg(),
        },
        async resolve(_root: any, args: any, ctx: any) {
          try {
            const userId = await getUserIdFromContext(ctx, strapi);
            if (!userId) {
              return {
                success: false,
                error: 'Authentication required',
              };
            }

            const { serviceId, serviceName, enabled, schedule } = args;

            // Check if setting already exists for this user and service
            const existing = await strapi.entityService.findMany('api::autostart.autostart-setting' as any, {
              filters: { user: userId, serviceId },
            });

            let setting;
            if (existing && existing.length > 0) {
              // Update existing
              setting = await strapi.entityService.update('api::autostart.autostart-setting' as any, (existing as any[])[0].id, {
                data: { serviceName, enabled, schedule },
              });
            } else {
              // Create new
              setting = await strapi.entityService.create('api::autostart.autostart-setting' as any, {
                data: { user: userId, serviceId, serviceName, enabled, schedule },
              });
            }

            return {
              success: true,
              setting,
            };
          } catch (error) {
            strapi.log.error('Error setting autostart setting:', error);
            return {
              success: false,
              error: (error as Error).message,
            };
          }
        },
      });

      t.nonNull.field('removeAutostartSetting', {
        type: 'RemoveAutostartSettingResponse',
        args: {
          id: nexus.nonNull(nexus.intArg()),
        },
        async resolve(_root: any, args: any, ctx: any) {
          try {
            const userId = await getUserIdFromContext(ctx, strapi);
            if (!userId) {
              return {
                success: false,
                message: 'Authentication required',
              };
            }

            const { id } = args;

            // Verify the setting belongs to the user
            const setting = await strapi.entityService.findOne('api::autostart.autostart-setting' as any, id, {
              populate: ['user'],
            });
            if (!setting || (setting as any).user.id !== userId) {
              return {
                success: false,
                message: 'Setting not found or access denied',
              };
            }

            await strapi.entityService.delete('api::autostart.autostart-setting' as any, id);

            return {
              success: true,
              message: 'Autostart setting removed successfully',
            };
          } catch (error) {
            strapi.log.error('Error removing autostart setting:', error);
            return {
              success: false,
              message: 'Failed to remove setting',
            };
          }
        },
      });
    },
  }),
];