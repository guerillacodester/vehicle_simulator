export default ({ strapi }: { strapi: any }) => {
  // Register the custom field on the server side
  strapi.customFields.register({
    name: 'action-button',
    plugin: 'action-buttons',
    type: 'json',
  });
};
