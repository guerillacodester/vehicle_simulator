/**
 * Admin entry point for allow-custom-files plugin (Strapi v5)
 */
export default {
  bootstrap(app: any) {
    console.log('[allow-custom-files Plugin] Bootstrapping...');
    
    // Wait for upload plugin to be available
    setTimeout(() => {
      const uploadPlugin = app.getPlugin?.('upload');
      
      if (!uploadPlugin?.utils?.validateFiles) {
        console.warn('[allow-custom-files] Upload plugin utils.validateFiles not found');
        return;
      }

      const customAllowed = [
        '.geojson',
        '.json',
        '.gtfs',
        '.zip',
        '.shp',
        '.pbf',
        '.tar',
        'application/geo+json',
        'application/vnd.geo+json',
        'application/octet-stream',
        'application/x-zip-compressed',
        'application/x-tar',
      ];

      // Override the upload validation
      uploadPlugin.utils.validateFiles = (files: File[]) =>
        files.map((file) => {
          const lower = file.name.toLowerCase();
          const mime = (file as any).type?.toLowerCase?.() ?? '';
          const matches = customAllowed.some(
            (ext) => lower.endsWith(ext) || mime.includes(ext)
          );

          if (matches) {
            (file as any).isValid = true;
            (file as any).errorMessage = null;
          }
          return file;
        });

      console.log('%c[allow-custom-files] ✅ Custom file validator ACTIVE (GeoJSON, GTFS, SHP, etc.)', 'color:#4ade80; font-weight:bold');
    }, 1000);
  },
};
