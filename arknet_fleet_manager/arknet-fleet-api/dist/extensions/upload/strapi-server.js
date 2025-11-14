"use strict";
/**
 * Upload plugin override - Add GeoJSON support
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.default = (plugin) => {
    var _a, _b;
    // Extend allowed file types to include GeoJSON
    if (plugin.config) {
        const originalIsValidFileType = (_b = (_a = plugin.services) === null || _a === void 0 ? void 0 : _a.upload) === null || _b === void 0 ? void 0 : _b.isValidFileType;
        if (originalIsValidFileType) {
            plugin.services.upload.isValidFileType = (file) => {
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
//# sourceMappingURL=strapi-server.js.map