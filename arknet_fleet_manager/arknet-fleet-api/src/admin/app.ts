const config = {
  locales: [
    // https://docs.strapi.io/developer-docs/latest/development/admin-customization.html#configuration
  ],
};

const bootstrap = (app: any) => {
  console.log('Strapi admin initialized');
};

export default {
  config,
  bootstrap,
};