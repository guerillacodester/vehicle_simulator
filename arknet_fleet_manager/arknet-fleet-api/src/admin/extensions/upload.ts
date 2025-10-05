/**
 * Admin Panel Extension - Override Upload Plugin
 * This properly extends the upload plugin to accept GeoJSON files
 */

export default {
  config: {
    // Override file upload restrictions
    file: {
      allowedMimeTypes: [
        // Images
        'image/jpeg',
        'image/png', 
        'image/gif',
        'image/svg+xml',
        'image/webp',
        // Videos
        'video/mp4',
        'video/mpeg',
        'video/webm',
        // Audio
        'audio/mpeg',
        'audio/wav',
        'audio/ogg',
        // Documents
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        // GeoJSON - THIS IS THE KEY ADDITION
        'application/json',
        'application/geo+json',
        'application/vnd.geo+json',
        'text/plain',
        'text/json'
      ],
      allowedExtensions: [
        // Images
        'jpg', 'jpeg', 'png', 'gif', 'svg', 'webp',
        // Videos
        'mp4', 'mpeg', 'webm',
        // Audio
        'mp3', 'wav', 'ogg',
        // Documents
        'pdf', 'doc', 'docx', 'xls', 'xlsx',
        // GeoJSON - THIS IS THE KEY ADDITION
        'json', 'geojson'
      ]
    }
  }
};
