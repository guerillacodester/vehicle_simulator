interface UploadPlugin {
  utils?: {
    validateFiles?: (files: File[]) => File[];
  };
}

export default {
  bootstrap(app: any) {
    const uploadPlugin = app.getPlugin('upload') as UploadPlugin | undefined;

    if (!uploadPlugin?.utils?.validateFiles) {
      console.warn('[Admin] ⚠️ Upload plugin not found or changed.');
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

    console.log('%c[Admin] ✅ Custom file validator active (GeoJSON, GTFS, SHP, etc.)', 'color:#4ade80');
  },
};
