/**
 * agency controller - with debug logging
 */

import { factories } from '@strapi/strapi'

export default factories.createCoreController('api::agency.agency' as any, ({ strapi }: any) => ({
  async find(ctx: any) {
    // Debug: log user state
    strapi.log.info('[agency.find] ========== CONTROLLER CALLED ==========');
    strapi.log.info('[agency.find] User:', ctx.state.user?.id, ctx.state.user?.username);
    strapi.log.info('[agency.find] User profile:', !!ctx.state.user?.profile);
    strapi.log.info('[agency.find] Access tier:', ctx.state.user?.profile?.access_tier?.name);
    
    // Call the default find method
    const { data, meta } = await super.find(ctx);
    return { data, meta };
  }
}));
