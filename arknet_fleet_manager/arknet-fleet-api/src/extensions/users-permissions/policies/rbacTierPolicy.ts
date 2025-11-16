// RBAC Permission Policy Middleware for Strapi
// Checks if user's access tier has the required permission or level for content type operation

type TierCode = string; // Now dynamic from DB

interface AccessTier {
  code: string;
  name: string;
  [key: string]: any; // For dynamic permissions and levels
}

export default (contentType: string, operation: string) => {
  return async (ctx: any, next: any) => {
    const user = ctx.state.user;
    if (!user || !user.profile || !user.profile.access_tier) {
      return ctx.forbidden('Access denied: no user profile or access tier found');
    }
    const accessTier: AccessTier = user.profile.access_tier;

    // First, check specific permission if exists
    const specificPerm = `can_${operation}_${contentType}`;
    if (accessTier[specificPerm] !== undefined) {
      if (!accessTier[specificPerm]) {
        return ctx.forbidden(`Access denied: ${accessTier.name} tier lacks permission '${specificPerm}'`);
      }
      await next();
      return;
    }

    // Otherwise, check level
    const levelField = `${contentType}_${operation}_level`;
    const requiredLevel = accessTier[levelField];
    if (!requiredLevel) {
      return ctx.forbidden(`Access denied: no level defined for ${contentType} ${operation}`);
    }

    // Fetch all tiers from DB to build level map
    const tiers = await (strapi as any).entityService.findMany('api::access-tier.access-tier', {
      fields: ['code', 'level'],
      sort: { level: 'asc' },
    });

    const tierLevels: Record<string, number> = {};
    tiers.forEach((tier: any) => {
      tierLevels[tier.code] = tier.level;
    });

    const userLevel = tierLevels[accessTier.code] || 0;
    const reqLevel = tierLevels[requiredLevel] || tierLevels['superadmin'] || 6;

    if (userLevel < reqLevel) {
      return ctx.forbidden(`Access denied: ${accessTier.name} tier insufficient for ${contentType} ${operation} (requires ${requiredLevel})`);
    }

    await next();
  };
};
