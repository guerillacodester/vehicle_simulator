// Strapi users-permissions plugin controller override: inject tier into JWT

export default ({ strapi }: any) => ({
  async callback(ctx: any) {
    const provider = ctx.params.provider || 'local';
    
    // Only handle local provider, others not supported in this override
    if (provider !== 'local') {
      return ctx.badRequest('Provider not supported');
    }

      // Local login with tier injection
      const params = ctx.request.body;

      if (!params.identifier) {
        return ctx.badRequest('identifier.missing');
      }

      if (!params.password) {
        return ctx.badRequest('password.missing');
      }

      const user: any = await strapi.query('plugin::users-permissions.user').findOne({
        where: {
          provider: 'local',
          $or: [{ email: params.identifier.toLowerCase() }, { username: params.identifier }],
        },
      });

      if (!user) {
        return ctx.badRequest('identifier.invalid');
      }

      const validPassword = await strapi.plugin('users-permissions').service('user').validatePassword(
        params.password,
        user.password
      );

      if (!validPassword) {
        return ctx.badRequest('password.invalid');
      }

      if (user.blocked) {
        return ctx.badRequest('blocked');
      }

      // Determine tier from user profile
      let tier = 'Guest';
      try {
        // Direct database query to get access_tier_id from user_profiles via link table
        const result: any = await strapi.db.connection.raw(`
          SELECT at.name as tier_name
          FROM user_profiles_user_lnk upl
          JOIN user_profiles_access_tier_lnk upatl ON upl.user_profile_id = upatl.user_profile_id
          JOIN access_tiers at ON upatl.access_tier_id = at.id
          WHERE upl.user_id = ?
          ORDER BY upatl.id DESC
          LIMIT 1
        `, [user.id]);
        
        strapi.log.info(`[auth] User ${user.username} raw query result:`, JSON.stringify(result, null, 2));
        
        if (result?.rows?.[0]?.tier_name) {
          tier = result.rows[0].tier_name;
          strapi.log.info(`[auth] Tier resolved to: ${tier}`);
        } else {
          strapi.log.info(`[auth] No tier found for user`);
        }
      } catch (err) {
        strapi.log.error('[auth] Error resolving tier:', err);
      }

      const jwt = strapi.plugin('users-permissions').service('jwt').issue({
        id: user.id,
        username: user.username,
        tier
      });

    ctx.send({
      jwt,
      user: await strapi.contentAPI.sanitize.output(user, strapi.getModel('plugin::users-permissions.user'), { auth: ctx.state.auth })
    });
  },
  
  // Placeholder methods - not implemented in this override
  async register(ctx: any) {
    return ctx.badRequest('Registration not implemented in override');
  },
  
  async resetPassword(ctx: any) {
    return ctx.badRequest('Reset password not implemented in override');
  },
  
  async connect(ctx: any) {
    return ctx.badRequest('Connect not implemented in override');
  },
  
  async forgotPassword(ctx: any) {
    return ctx.badRequest('Forgot password not implemented in override');
  },
  
  async emailConfirmation(ctx: any) {
    return ctx.badRequest('Email confirmation not implemented in override');
  },
  
  async sendEmailConfirmation(ctx: any) {
    return ctx.badRequest('Send email confirmation not implemented in override');
  },
  
  async changePassword(ctx: any) {
    return ctx.badRequest('Change password not implemented in override');
  },
  
  async refresh(ctx: any) {
    return ctx.badRequest('Token refresh not implemented in override');
  },
  
  async logout(ctx: any) {
    return ctx.badRequest('Logout not implemented in override');
  }
});
