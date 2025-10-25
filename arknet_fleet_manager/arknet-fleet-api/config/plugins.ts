export default ({ env }: any) => ({
  upload: {
    config: {
      // Choose provider: Cloudinary or Local
      provider: env('UPLOAD_PROVIDER', 'cloudinary'),
      providerOptions:
        env('UPLOAD_PROVIDER', 'cloudinary') === 'cloudinary'
          ? {
            cloud_name: env('CLOUDINARY_NAME'),
            api_key: env('CLOUDINARY_KEY'),
            api_secret: env('CLOUDINARY_SECRET'),
          }
          : {
            localServer: { maxage: 300000 },
          },

      // Upload actions
      actionOptions:
        env('UPLOAD_PROVIDER', 'cloudinary') === 'cloudinary'
          ? {
            upload: {
              resource_type: 'raw', // accept any file type (non-media)
              folder: env('CLOUDINARY_FOLDER', 'strapi-uploads'),
            },
            delete: {},
          }
          : {},

      // General settings
      sizeLimit: 1000 * 1024 * 1024, // 1000 MB
      formats: ['thumbnail', 'large', 'medium', 'small'],
      breakpoints: {
        xlarge: 1920,
        large: 1000,
        medium: 750,
        small: 500,
        xsmall: 64,
      },
    },
  },
  // ==============================
  // CUSTOM ADMIN PLUGIN
  // ==============================
  'allow-custom-files': {
    enabled: true,
    resolve: './src/plugins/allow-custom-files',
  },
  'action-buttons': {
    enabled: true,
    resolve: './src/plugins/strapi-plugin-action-buttons'
  },
});
