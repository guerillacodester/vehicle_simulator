/**
 * Z-index layers for map UI components
 * Ensures proper stacking order without conflicts
 */
export const MAP_Z_INDEX = {
  MAP_BASE: 1,
  MAP_TILES: 400,
  LEAFLET_CONTROLS: 1000,
  HAMBURGER_BUTTON: 1001,
  CONTROL_PANEL: 1002,
} as const;

/**
 * Map configuration constants
 */
export const MAP_CONFIG = {
  DEFAULT_CENTER: [13.2, -59.55] as [number, number],
  DEFAULT_ZOOM: 10,
  MIN_ZOOM: 5,
  MAX_ZOOM: 18,
  TILE_MAX_ZOOM: 19,
  TILE_URL: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
  ATTRIBUTION: '&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; OpenStreetMap contributors',
} as const;

/**
 * Animation/timing constants
 */
export const ANIMATION = {
  PANEL_SLIDE_MS: 260,
  SCALE_CHECK_DELAY_MS: 100,
} as const;
