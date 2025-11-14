export default [
  // --- Core middleware order ---
  'strapi::logger',
  'strapi::errors',

  // --- Security middleware ---
  {
    name: 'strapi::security',
    config: {
      contentSecurityPolicy: {
        useDefaults: true,
        directives: {
          // allow script & style CDNs you use in admin UI
          'script-src': [
            "'self'",
            "'unsafe-inline'",
            'https://unpkg.com',
            'https://cdnjs.cloudflare.com',
            'https://cdn.jsdelivr.net',
          ],
          'style-src': [
            "'self'",
            "'unsafe-inline'",
            'https://unpkg.com',
            'https://cdnjs.cloudflare.com',
            'https://cdn.jsdelivr.net',
          ],
          'img-src': [
            "'self'",
            'data:',
            'blob:',
            'https://market-assets.strapi.io',
            'https://*.tile.openstreetmap.org',
          ],
          'connect-src': ["'self'", 'https:'],
          'media-src': ["'self'", 'data:', 'blob:', 'https:'],
        },
      },

      // ✅ Allow GeoJSON, JSON, text & CSV uploads globally
      allowedMimeTypes: [
        'image/*',
        'video/*',
        'audio/*',
        'text/plain',
        'text/csv',
        'application/json',
        'application/geo+json',
        'application/geojson',
        'application/octet-stream', // fallback for "raw" Cloudinary files
      ],
    },
  },

  // --- Standard Strapi middleware chain ---
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
        maxFileSize: 1000 * 1024 * 1024, // 1000 MB
      },
    },
  },
  'strapi::session',
  'strapi::favicon',
  'strapi::public',
];
