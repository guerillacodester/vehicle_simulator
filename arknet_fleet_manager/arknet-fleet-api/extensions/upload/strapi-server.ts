/**
 * Upload plugin override - Add GeoJSON support
 */

export default (plugin: any) => {
  // Extend allowed file types to include GeoJSON
  if (plugin.config) {
    const originalIsValidFileType = plugin.services?.upload?.isValidFileType;
    
    if (originalIsValidFileType) {
      plugin.services.upload.isValidFileType = (file: any) => {
        // Allow .geojson files
        if (file.name && file.name.toLowerCase().endsWith('.geojson')) {
          return true;
        }
        
        // Fall back to original validation
        return originalIsValidFileType(file);
      };
    }
  }
  
  return plugin;
};
