import { mergeConfig, type UserConfig } from 'vite';

export default (config: UserConfig) => {
  // Important: always return the modified config
  return mergeConfig(config, {
    resolve: {
      alias: {
        '@': '/src',
      },
    },
    // Allow GeoJSON files specifically (not all .json to avoid conflicts)
    assetsInclude: ['**/*.geojson'],
  });
};
