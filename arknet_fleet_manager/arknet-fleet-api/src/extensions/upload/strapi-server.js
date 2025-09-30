const _ = require('lodash');

module.exports = (plugin) => {
  // Extend the allowed file types to include GeoJSON
  const originalIsValidFileType = plugin.services.upload.isValidFileType;
  
  plugin.services.upload.isValidFileType = function(file, allowedTypes) {
    // Allow .geojson files
    if (file.name && file.name.toLowerCase().endsWith('.geojson')) {
      return true;
    }
    
    // Allow application/json MIME type for GeoJSON
    if (file.type === 'application/json' || file.type === 'application/geo+json') {
      return true;
    }
    
    // Fall back to original validation
    return originalIsValidFileType.call(this, file, allowedTypes);
  };

  return plugin;
};