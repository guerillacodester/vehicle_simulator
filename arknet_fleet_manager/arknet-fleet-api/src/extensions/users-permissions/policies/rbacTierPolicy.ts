// RBAC Tier Policy Middleware for Strapi
// Returns 403 Forbidden if user's tier is insufficient

export default (requiredTier: string) => {
  return async (ctx: any, next: any) => {
    const user = ctx.state.user;
    if (!user || !user.tier) {
      return ctx.forbidden('Access denied: no user tier found');
    }
    const tiers = ['Guest', 'Dispatcher', 'Admin'];
    const userTierIdx = tiers.indexOf(user.tier);
    const requiredTierIdx = tiers.indexOf(requiredTier);
    if (userTierIdx < 0 || requiredTierIdx < 0 || userTierIdx < requiredTierIdx) {
      return ctx.forbidden(`Access denied: ${user.tier} tier insufficient for ${requiredTier}`);
    }
    await next();
  };
};
