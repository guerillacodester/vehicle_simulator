import uploadGeojsonExtension from './extensions/upload-geojson';

const config = {
  locales: [
    // https://docs.strapi.io/developer-docs/latest/development/admin-customization.html#configuration
  ],
};

const bootstrap = (app: any) => {
  console.log('[Admin] Strapi admin initialized');
  // Register the upload-geojson extension to patch the upload plugin
  if (uploadGeojsonExtension && uploadGeojsonExtension.register) {
    uploadGeojsonExtension.register(app);
  }
  console.log('[Admin] ✅ GeoJSON file uploads enabled (.json, .geojson)');
};

export default {
  config,
  bootstrap,
};