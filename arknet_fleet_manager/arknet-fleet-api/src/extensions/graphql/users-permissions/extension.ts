// GraphQL extension to expose 'tier' field on UsersPermissionsUser and UsersPermissionsMe types
import type { Core } from '@strapi/strapi';

const tierResolver = async (user: any, _args: any, context: any) => {
  if (!user) return 'Guest';

  // First try to get the enriched user from context (populated by populateUserProfile middleware)
  const contextUser = context?.state?.user || context?.user;
  
  if (contextUser?.profile?.access_tier) {
    const tier = contextUser.profile.access_tier.name || contextUser.profile.access_tier.tier;
    if (tier) {
      console.log(`[GraphQL] Tier from context middleware: ${tier}`);
      return tier;
    }
  }

  // Fallback: If tier/name is directly on user object (legacy/support)
  if (user.tier) return user.tier;

  // Fallback: If user already populated access_tier relation
  if (user.access_tier && (user.access_tier.name || user.access_tier.tier)) {
    return user.access_tier.name || user.access_tier.tier;
  }

  // Fallback: If profile relation contains access_tier
  if (user.profile && user.profile.access_tier && (user.profile.access_tier.name || user.profile.access_tier.tier)) {
    return user.profile.access_tier.name || user.profile.access_tier.tier;
  }

  // Last resort: Query user-profile separately since it's not a direct relation on user entity
  if (user.id && context?.strapi) {
    try {
      console.log('[GraphQL] Falling back to database query for tier');
      // Query via link table since user relation uses a join table
      const userProfile = await context.strapi.db.connection.raw(`
        SELECT at.name as tier_name
        FROM user_profiles_user_lnk upl
        JOIN user_profiles_access_tier_lnk upatl ON upl.user_profile_id = upatl.user_profile_id
        JOIN access_tiers at ON upatl.access_tier_id = at.id
        WHERE upl.user_id = ?
        ORDER BY upatl.id DESC
        LIMIT 1
      `, [user.id]);
      
      if (userProfile?.rows?.[0]?.tier_name) {
        return userProfile.rows[0].tier_name;
      }
    } catch (err) {
      console.error('[GraphQL] Error fetching user tier:', err);
    }
  }

  return 'Guest';
};

export default ({ nexus, strapi }: { nexus: any; strapi: Core.Strapi }) => ({
  types: [
    nexus.extendType({
      type: 'UsersPermissionsUser',
      definition(t: any) {
        t.string('tier', {
          resolve: (user: any, args: any, context: any) => tierResolver(user, args, { ...context, strapi }),
        });
      },
    }),
    nexus.extendType({
      type: 'UsersPermissionsMe',
      definition(t: any) {
        t.string('tier', {
          resolve: (user: any, args: any, context: any) => tierResolver(user, args, { ...context, strapi }),
        });
      },
    }),
  ],
});
