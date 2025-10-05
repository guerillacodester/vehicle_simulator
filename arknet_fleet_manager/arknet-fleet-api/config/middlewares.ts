export default [
  'strapi::logger',
  'strapi::errors',
  {
    name: 'strapi::security',
    config: {
      contentSecurityPolicy: {
        useDefaults: true,
        directives: {
          'script-src': ["'self'", "'unsafe-inline'", 'https://unpkg.com', 'https://cdnjs.cloudflare.com', 'https://cdn.jsdelivr.net'],
          'style-src': ["'self'", "'unsafe-inline'", 'https://unpkg.com', 'https://cdnjs.cloudflare.com', 'https://cdn.jsdelivr.net'],
          'img-src': ["'self'", 'data:', 'blob:', 'https://market-assets.strapi.io', 'https://*.tile.openstreetmap.org'],
        },
      },
      // Allow GeoJSON file uploads (application/json, application/geo+json)
      allowedFileTypes: ['image', 'video', 'audio', 'file'],
    },
  },
  'strapi::cors',
  'strapi::poweredBy',
  'strapi::query',
  {
    name: 'strapi::body',
    config: {
      formLimit: '256mb',
      jsonLimit: '256mb',
      textLimit: '256mb',
      formidable: {
        maxFileSize: 200 * 1024 * 1024, // 200mb
      },
    },
  },
  'strapi::session',
  'strapi::favicon',
  'strapi::public',
];
