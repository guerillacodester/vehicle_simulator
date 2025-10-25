/**
 * Server entry for allow-custom-files plugin (Strapi v5)
 */
export default {
  register({ strapi }: any) {
    console.log('[allow-custom-files Plugin] Server registered');
  },
  bootstrap({ strapi }: any) {
    console.log('[allow-custom-files Plugin] Server bootstrapped');
  },
};
