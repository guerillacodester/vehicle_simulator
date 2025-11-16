/**
 * Middleware to populate user profile and access tier after JWT authentication
 * Runs after users-permissions authentication, enriches ctx.state.user
 */

export default () => {
  return async (ctx: any, next: any) => {
    // Only run if user is authenticated
    if (ctx.state.user) {
      const userId = ctx.state.user.id;
      
      (strapi as any).log.info(`[populateUserProfile] Loading profile for user ${userId}`);
      
      try {
        // Use direct database query to get profile ID from join table
        const result: any = await (strapi as any).db.connection.raw(`
          SELECT up.id as profile_id
          FROM user_profiles up
          JOIN user_profiles_user_lnk uul ON up.id = uul.user_profile_id
          WHERE uul.user_id = ?
          LIMIT 1
        `, [userId]);
        
        if (result?.rows?.[0]?.profile_id) {
          const profileId = result.rows[0].profile_id;
          (strapi as any).log.info(`[populateUserProfile] Found profile ${profileId} for user ${userId}`);
          
          // Now fetch the full profile with access_tier populated
          const profile: any = await (strapi as any).entityService.findOne('api::user-profile.user-profile', profileId, {
            populate: {
              access_tier: true
            }
          });
          
          if (profile && profile.access_tier) {
            ctx.state.user.profile = profile;
            (strapi as any).log.info(`[populateUserProfile] User ${userId} profile loaded with tier: ${profile.access_tier.name} (level ${profile.access_tier.level})`);
          } else {
            (strapi as any).log.warn(`[populateUserProfile] Profile ${profileId} found but no access_tier`);
          }
        } else {
          (strapi as any).log.warn(`[populateUserProfile] No profile found for user ${userId}`);
        }
      } catch (error: any) {
        (strapi as any).log.error(`[populateUserProfile] Error fetching profile for user ${userId}:`, error?.message || error);
      }
    }
    
    await next();
  };
};
