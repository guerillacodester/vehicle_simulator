module.exports = ({ nexus, strapi }) => [
  // Define AutostartSetting type
  nexus.objectType({
    name: 'AutostartSetting',
    definition(t) {
      t.nonNull.id('id');
      t.nonNull.string('serviceId');
      t.nonNull.string('serviceName');
      t.nonNull.boolean('enabled');
      t.string('schedule');
      t.field('createdAt', { type: 'DateTime' });
      t.field('updatedAt', { type: 'DateTime' });
    },
  }),

  // Define AutostartSettingsResponse type
  nexus.objectType({
    name: 'AutostartSettingsResponse',
    definition(t) {
      t.nonNull.boolean('success');
      t.nonNull.list.nonNull.field('settings', { type: 'AutostartSetting' });
    },
  }),

  // Define SetAutostartSettingResponse type
  nexus.objectType({
    name: 'SetAutostartSettingResponse',
    definition(t) {
      t.nonNull.boolean('success');
      t.field('setting', { type: 'AutostartSetting' });
      t.string('error');
    },
  }),

  // Define RemoveAutostartSettingResponse type
  nexus.objectType({
    name: 'RemoveAutostartSettingResponse',
    definition(t) {
      t.nonNull.boolean('success');
      t.nonNull.string('message');
    },
  }),

  // Extend Query type with autostartSettings field
  nexus.extendType({
    type: 'Query',
    definition(t) {
      t.nonNull.field('autostartSettings', {
        type: 'AutostartSettingsResponse',
        async resolve(_root, _args, ctx) {
          try {
            const userId = ctx.state.user?.id;
            // if (!userId) {
            //   throw new Error('Authentication required');
            // }

            const settings = await strapi.entityService.findMany('api::autostart-setting.autostart-setting', {
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
    definition(t) {
      t.nonNull.field('setAutostartSetting', {
        type: 'SetAutostartSettingResponse',
        args: {
          serviceId: nexus.nonNull(nexus.stringArg()),
          serviceName: nexus.nonNull(nexus.stringArg()),
          enabled: nexus.nonNull(nexus.booleanArg()),
          schedule: nexus.stringArg(),
        },
        async resolve(_root, args, ctx) {
          try {
            const userId = ctx.state.user?.id;
            if (!userId) {
              return {
                success: false,
                error: 'Authentication required',
              };
            }

            const { serviceId, serviceName, enabled, schedule } = args;

            // Check if setting already exists for this user and service
            const existing = await strapi.entityService.findMany('api::autostart-setting.autostart-setting' as any, {
              filters: { user: userId, serviceId },
            });

            let setting;
            if (existing && existing.length > 0) {
              // Update existing
              setting = await strapi.entityService.update('api::autostart-setting.autostart-setting' as any, (existing as any[])[0].id, {
                data: { serviceName, enabled, schedule },
              });
            } else {
              // Create new
              setting = await strapi.entityService.create('api::autostart-setting.autostart-setting' as any, {
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
          id: nexus.nonNull(nexus.idArg()),
        },
        async resolve(_root: any, args: any, ctx: any) {
          try {
            const userId = ctx.state.user?.id;
            if (!userId) {
              return {
                success: false,
                message: 'Authentication required',
              };
            }

            const { id } = args;

            // Verify the setting belongs to the user
            const setting = await strapi.entityService.findOne('api::autostart-setting.autostart-setting' as any, id, {
              populate: ['user'],
            });
            if (!setting || (setting as any).user.id !== userId) {
              return {
                success: false,
                message: 'Setting not found or access denied',
              };
            }

            await strapi.entityService.delete('api::autostart-setting.autostart-setting' as any, id);

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