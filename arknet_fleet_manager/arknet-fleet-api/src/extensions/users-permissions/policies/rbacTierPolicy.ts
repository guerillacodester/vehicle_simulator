import { errors } from '@strapi/utils';

const { PolicyError } = errors;

type TierCode = string;

interface AccessTier {
  code: string;
  name: string;
  level: number;
  [key: string]: any;
}

const methodToOperation = (method: string): 'create' | 'read' | 'update' | 'delete' => {
  switch (method.toUpperCase()) {
    case 'POST':
      return 'create';
    case 'PUT':
    case 'PATCH':
      return 'update';
    case 'DELETE':
      return 'delete';
    default:
      return 'read';
  }
};

const loadProfileWithTier = async (strapi: any, userId: number) => {
  const result = await strapi.db.connection.raw(
    `SELECT 
       up.id as profile_id,
       at.*
     FROM user_profiles up
     JOIN user_profiles_user_lnk uul ON up.id = uul.user_profile_id
     JOIN user_profiles_access_tier_lnk uat ON up.id = uat.user_profile_id
     JOIN access_tiers at ON at.id = uat.access_tier_id
     WHERE uul.user_id = ?
     ORDER BY up.id DESC
     LIMIT 1`,
    [userId]
  );

  const row = result?.rows?.[0];
  if (!row || !row.profile_id) {
    return null;
  }

  // Return profile with access_tier containing all fields
  return {
    id: row.profile_id,
    access_tier: {
      id: row.id,
      name: row.name,
      code: row.code,
      level: row.level,
      description: row.description,
      can_manage_autostart: row.can_manage_autostart,
      can_view_services: row.can_view_services,
      can_create_users: row.can_create_users,
      can_manage_all_autostart: row.can_manage_all_autostart,
      can_create_access_tier: row.can_create_access_tier,
      can_read_access_tier: row.can_read_access_tier,
      can_update_access_tier: row.can_update_access_tier,
      can_delete_access_tier: row.can_delete_access_tier,
      can_create_user_profile: row.can_create_user_profile,
      can_read_user_profile: row.can_read_user_profile,
      can_update_user_profile: row.can_update_user_profile,
      can_delete_user_profile: row.can_delete_user_profile,
      can_create_agency: row.can_create_agency,
      can_read_agency: row.can_read_agency,
      can_update_agency: row.can_update_agency,
      can_delete_agency: row.can_delete_agency,
      can_create_vehicle: row.can_create_vehicle,
      can_read_vehicle: row.can_read_vehicle,
      can_update_vehicle: row.can_update_vehicle,
      can_delete_vehicle: row.can_delete_vehicle,
      can_create_route: row.can_create_route,
      can_read_route: row.can_read_route,
      can_update_route: row.can_update_route,
      can_delete_route: row.can_delete_route,
    },
  };
};

export default (policyContext: any, config: any, { strapi }: any) => {
  strapi.log.info(`[RBAC] ========== Policy loaded with config:`, config);
  
  return async (ctx: any, next: any) => {
    strapi.log.info(`[RBAC] ========== Policy invoked ==========`);
    strapi.log.info(`[RBAC] Method: ${ctx.request.method}, Path: ${ctx.request.path}`);
    strapi.log.info(`[RBAC] policyContext:`, typeof policyContext);
    
    // Ensure user is authenticated (manually, since routes set auth: false)
    let user = ctx.state.user;
    if (!user) {
      const tokenPayload = await strapi.plugin('users-permissions').service('jwt').getToken(ctx);
      if (!tokenPayload?.id) {
        throw new PolicyError('Missing or invalid authentication token');
      }

      user = await strapi.db.query('plugin::users-permissions.user').findOne({
        where: { id: tokenPayload.id },
      });

      if (!user) {
        throw new PolicyError('Authenticated user no longer exists');
      }

      ctx.state.user = user;
    }

    if (!ctx.state.user.profile || !ctx.state.user.profile.access_tier) {
      const profile = await loadProfileWithTier(strapi, ctx.state.user.id);
      if (!profile || !profile.access_tier) {
        throw new PolicyError('User profile or access tier is not configured');
      }
      ctx.state.user.profile = profile;
    }

    const accessTier: AccessTier = ctx.state.user.profile.access_tier;

    const contentTypeRaw = config?.contentType || ctx.state.route?.info?.apiName;
    if (!contentTypeRaw) {
      throw new PolicyError('RBAC policy misconfigured: missing content type');
    }
    const contentType = String(contentTypeRaw).replace(/-/g, '_');

    const operation = (config?.operation || methodToOperation(ctx.request.method)).toLowerCase();
    const specificPerm = `can_${operation}_${contentType}`;

    strapi.log.info(`[RBAC] Checking ${specificPerm} for tier ${accessTier.name} (${accessTier.code})`);
    strapi.log.info(`[RBAC] Permission value: ${accessTier[specificPerm]}`);
    strapi.log.info(`[RBAC] Access tier keys:`, Object.keys(accessTier));

    if (accessTier[specificPerm] === undefined) {
      if ((accessTier.code || '').toLowerCase() === 'superadmin') {
        strapi.log.info(`[RBAC] Allowing SuperAdmin fallback`);
        await next();
        return;
      }
      throw new PolicyError(`Permission '${specificPerm}' not defined for tier ${accessTier.name}`);
    }

    if (!accessTier[specificPerm]) {
      throw new PolicyError(`Tier ${accessTier.name} lacks permission '${specificPerm}'`);
    }

    strapi.log.info(`[RBAC] Permission granted: ${specificPerm}`);

    await next();
  };
};
