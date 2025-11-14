module.exports = {
  async getAll() {
    return await strapi.entityService.findMany('api::access-tier.access-tier', {});
  },
  async getById(id) {
    return await strapi.entityService.findOne('api::access-tier.access-tier', id, {});
  }
};
