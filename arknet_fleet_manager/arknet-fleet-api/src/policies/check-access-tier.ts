/**
 * check-access-tier policy
 * 
 * Enforces RBAC by checking user's AccessTier against endpoint requirements.
 * 
 * Usage in routes:
 *   config: {
 *     policies: [
 *       { name: 'global::check-access-tier', config: { minTier: 'Manager' } }
 *     ]
 *   }
 * 
 * Or for specific tier allowlist:
 *   config: {
 *     policies: [
 *       { name: 'global::check-access-tier', config: { allowedTiers: ['Admin', 'SuperAdmin'] } }
 *     ]
 *   }
 */

export default (policyContext: any, config: any, { strapi }: any) => {
  return async (ctx: any, next: any) => {
    // Tier hierarchy (higher index = higher privilege)
    const tierHierarchy = [
      'Guest',
      'Viewer',
      'Operator',
      'Dispatcher',
      'Manager',
      'Admin',
      'SuperAdmin'
    ];

    // Ensure user is authenticated
    if (!ctx.state.user) {
      strapi.log.warn('[check-access-tier] Unauthenticated request');
      return ctx.unauthorized('Authentication required');
    }

    const userId = ctx.state.user.id;

    try {
      // Load user profile with access_tier relation
      const profiles = await strapi.entityService.findMany(
        'api::user-profile.user-profile',
        {
          filters: { user: userId },
          populate: ['access_tier']
        }
      );

      if (!profiles || profiles.length === 0) {
        strapi.log.warn(`[check-access-tier] No profile found for user ${userId}`);
        return ctx.forbidden('User profile not found');
      }

      const userProfile = profiles[0];
      const accessTier = userProfile.access_tier;

      if (!accessTier || !accessTier.name) {
        strapi.log.warn(`[check-access-tier] No access tier assigned to user ${userId}`);
        return ctx.forbidden('Access tier not assigned');
      }

      const userTierName = accessTier.name;
      const userTierIndex = tierHierarchy.indexOf(userTierName);

      if (userTierIndex === -1) {
        strapi.log.error(`[check-access-tier] Unknown tier: ${userTierName}`);
        return ctx.forbidden('Invalid access tier');
      }

      // Check against minTier (hierarchy-based)
      if (config.minTier) {
        const requiredTierIndex = tierHierarchy.indexOf(config.minTier);
        if (requiredTierIndex === -1) {
          strapi.log.error(`[check-access-tier] Invalid minTier config: ${config.minTier}`);
          return ctx.forbidden('Configuration error');
        }

        if (userTierIndex < requiredTierIndex) {
          strapi.log.warn(
            `[check-access-tier] Access denied for user ${userId} (tier: ${userTierName}, required: ${config.minTier})`
          );
          return ctx.forbidden(`Minimum tier required: ${config.minTier}`);
        }
      }

      // Check against allowedTiers (allowlist)
      if (config.allowedTiers && Array.isArray(config.allowedTiers)) {
        if (!config.allowedTiers.includes(userTierName)) {
          strapi.log.warn(
            `[check-access-tier] Access denied for user ${userId} (tier: ${userTierName}, allowed: ${config.allowedTiers.join(', ')})`
          );
          return ctx.forbidden(`Access restricted to: ${config.allowedTiers.join(', ')}`);
        }
      }

      // Access granted
      strapi.log.debug(`[check-access-tier] Access granted for user ${userId} (tier: ${userTierName})`);
      return next();
    } catch (error) {
      strapi.log.error('[check-access-tier] Error checking access tier:', error);
      return ctx.internalServerError('Error verifying access tier');
    }
  };
};
