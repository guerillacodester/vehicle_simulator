// Strapi Admin Panel Extension: Allow .geojson files in upload plugin
export default {
  register(app) {
    // Patch the upload plugin's file type validation
    app.addReducers({
      upload: (state = {}, action) => {
        if (action.type === 'UPLOAD_SET_ALLOWED_TYPES') {
          // Add .geojson and GeoJSON MIME types
          const newTypes = [
            ...action.allowedTypes,
            'application/geo+json',
            'application/vnd.geo+json',
            'application/json',
            '.geojson',
            '.json',
            'text/plain',
            'text/json'
          ];
          return { ...state, allowedTypes: Array.from(new Set(newTypes)) };
        }
        return state;
      }
    });
    console.info('[Admin Extension] .geojson file support enabled in upload plugin');
  },
};
