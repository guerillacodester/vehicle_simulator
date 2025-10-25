/**
 * Admin Upload Plugin Extension (Strapi v5)
 * Ensures the Media Library accepts GeoJSON by MIME and extension.
 */

export default {
  config: {
    file: {
      // Extend allowed MIME types used by the Admin UI validator
      allowedMimeTypes: [
        // Common
        'application/json',
        'text/plain',
        'text/json',
        // GeoJSON (RFC 7946 and vendor)
        'application/geo+json',
        'application/vnd.geo+json',
        // Keep image/audio/video/doc defaults to avoid narrowing
        'image/jpeg', 'image/png', 'image/gif', 'image/svg+xml', 'image/webp',
        'video/mp4', 'video/mpeg', 'video/webm',
        'audio/mpeg', 'audio/wav', 'audio/ogg',
        'application/pdf',
      ],
      // Extend allowed extensions used by the Admin UI validator
      allowedExtensions: [
        'json', 'geojson',
        // Keep common defaults
        'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp',
        'mp4', 'mpeg', 'webm',
        'mp3', 'wav', 'ogg',
        'pdf', 'doc', 'docx', 'xls', 'xlsx',
      ],
    },
  },
  register(app: any) {
    console.info('[Admin Upload Extension] ✅ GeoJSON (.geojson) enabled in Media Library');
  },
};
