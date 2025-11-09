/**
 * Extended Leaflet type definitions
 * Provides type safety for Leaflet operations
 */

export interface LeafletLatLng {
  lat: number;
  lng: number;
}

export interface LeafletBounds {
  pad(bufferRatio: number): LeafletBounds;
  isValid(): boolean;
}

export interface LeafletLayer {
  addTo(map: LeafletMap): this;
  remove(): this;
}

export interface LeafletLayerGroup extends LeafletLayer {
  clearLayers(): this;
  getBounds(): LeafletBounds | undefined;
  addLayer(layer: LeafletLayer): this;
  removeLayer(layer: LeafletLayer): this;
}

export interface LeafletMarker extends LeafletLayer {
  bindPopup(content: string): this;
  getLatLng(): LeafletLatLng;
}

export interface LeafletMap {
  remove(): void;
  invalidateSize(options?: { animate?: boolean }): this;
  fitBounds(bounds: LeafletBounds, options?: Record<string, unknown>): this;
  setView(center: [number, number], zoom?: number): this;
  on(event: string, handler: (...args: unknown[]) => void): this;
  off(event?: string, handler?: (...args: unknown[]) => void): this;
}

export interface LeafletTileLayer extends LeafletLayer {
  setUrl(url: string): this;
}

export interface LeafletControl extends LeafletLayer {
  getContainer(): HTMLElement | undefined;
}

export interface LeafletStatic {
  map(element: HTMLElement, options?: MapOptions): LeafletMap;
  tileLayer(urlTemplate: string, options?: TileLayerOptions): LeafletTileLayer;
  marker(latlng: [number, number], options?: Record<string, unknown>): LeafletMarker;
  layerGroup(layers?: LeafletLayer[]): LeafletLayerGroup;
  control: {
    scale(options?: ScaleControlOptions): LeafletControl;
    zoom(options?: ZoomControlOptions): LeafletControl;
  };
}

export interface MapOptions {
  center?: [number, number];
  zoom?: number;
  minZoom?: number;
  maxZoom?: number;
  zoomControl?: boolean;
  scrollWheelZoom?: boolean;
}

export interface TileLayerOptions {
  attribution?: string;
  maxZoom?: number;
  minZoom?: number;
}

export interface ScaleControlOptions {
  position?: 'topleft' | 'topright' | 'bottomleft' | 'bottomright';
  maxWidth?: number;
  metric?: boolean;
  imperial?: boolean;
  updateWhenIdle?: boolean;
}

export interface ZoomControlOptions {
  position?: 'topleft' | 'topright' | 'bottomleft' | 'bottomright';
}

/**
 * Type guard to check if Leaflet is loaded
 */
export function isLeafletLoaded(): boolean {
  return typeof window !== 'undefined' && 'L' in window;
}

/**
 * Get Leaflet global instance
 */
export function getLeaflet(): LeafletStatic | null {
  if (!isLeafletLoaded()) return null;
  return (window as unknown as { L: LeafletStatic }).L;
}
