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
      }
    }
  }
});
