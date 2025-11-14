module.exports = {
  async find(ctx) {
    return await strapi.entityService.findMany('api::access-tier.access-tier', {});
  },
  async findOne(ctx) {
    const { id } = ctx.params;
    return await strapi.entityService.findOne('api::access-tier.access-tier', id, {});
  },
  async create(ctx) {
    const data = ctx.request.body;
    return await strapi.entityService.create('api::access-tier.access-tier', { data });
  },
  async update(ctx) {
    const { id } = ctx.params;
    const data = ctx.request.body;
    return await strapi.entityService.update('api::access-tier.access-tier', id, { data });
  },
  async delete(ctx) {
    const { id } = ctx.params;
    return await strapi.entityService.delete('api::access-tier.access-tier', id);
  }
};
