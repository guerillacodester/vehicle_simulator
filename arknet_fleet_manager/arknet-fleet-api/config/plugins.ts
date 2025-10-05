export default () => ({
  upload: {
    config: {
      sizeLimit: 200 * 1024 * 1024, // 200mb
      formats: ['thumbnail', 'large', 'medium', 'small'],
      breakpoints: {
        xlarge: 1920,
        large: 1000,
        medium: 750,
        small: 500,
        xsmall: 64
      },
      // Allow GeoJSON file uploads
      providerOptions: {
        localServer: {
          maxage: 300000
        }
      },
      // Explicitly allow GeoJSON files
      allowedFormats: [
        'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'image/webp',
        'video/mp4', 'video/mpeg', 'video/webm',
        'audio/mpeg', 'audio/wav', 'audio/ogg',
        'application/pdf',
        'application/json',           // GeoJSON
        'application/geo+json',        // GeoJSON standard MIME
        'application/vnd.geo+json',    // GeoJSON vendor MIME
        'text/plain'                   // Sometimes GeoJSON is served as text
      ]
    }
  }
});
