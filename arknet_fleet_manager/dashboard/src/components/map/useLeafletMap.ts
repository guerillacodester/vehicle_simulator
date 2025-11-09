import { useEffect, useRef, useCallback } from 'react';
import type { LeafletMap } from './leafletTypes';
import { getLeafletGlobal } from './useLeafletLoader';
import { MAP_CONFIG } from './mapConstants';

interface UseLeafletMapOptions {
  containerRef: React.RefObject<HTMLDivElement>;
  center?: [number, number];
  zoom?: number;
  onMapReady?: (map: LeafletMap) => void;
}

/**
 * Custom hook to initialize and manage Leaflet map instance
 * Handles map lifecycle and configuration
 */
export function useLeafletMap({
  containerRef,
  center = MAP_CONFIG.DEFAULT_CENTER,
  zoom = MAP_CONFIG.DEFAULT_ZOOM,
  onMapReady,
}: UseLeafletMapOptions) {
  const mapRef = useRef<LeafletMap | null>(null);

  const initializeMap = useCallback(() => {
    console.log('[useLeafletMap] initializeMap called', {
      hasLeaflet: !!getLeafletGlobal(),
      hasContainer: !!containerRef.current,
      hasExistingMap: !!mapRef.current
    });
    
    const L = getLeafletGlobal();
    if (!L) {
      console.error('[useLeafletMap] Leaflet not loaded!');
      return;
    }
    if (!containerRef.current) {
      console.error('[useLeafletMap] Container ref not set!');
      return;
    }
    if (mapRef.current) {
      console.log('[useLeafletMap] Map already exists');
      return;
    }

    try {
      console.log('[useLeafletMap] Creating Leaflet map...');
      const map = L.map(containerRef.current, {
        center,
        zoom,
        minZoom: MAP_CONFIG.MIN_ZOOM,
        maxZoom: MAP_CONFIG.MAX_ZOOM,
        zoomControl: false, // Disable default zoom control
      });
      
      // Add zoom control at bottom-right (away from hamburger at top-left)
      L.control.zoom({
        position: 'bottomright'
      }).addTo(map);

      // Add tile layer
      L.tileLayer(MAP_CONFIG.TILE_URL, {
        attribution: MAP_CONFIG.ATTRIBUTION,
        maxZoom: MAP_CONFIG.TILE_MAX_ZOOM,
      }).addTo(map);

      // Add scale control at top-right
      L.control.scale({
        position: 'topright',
        imperial: true,
        metric: true,
        maxWidth: 150,
      }).addTo(map);

      mapRef.current = map;
      console.log('[useLeafletMap] Map created successfully!', map);
      onMapReady?.(map);
    } catch (error) {
      console.error('[useLeafletMap] Failed to initialize map:', error);
    }
  }, [containerRef, center, zoom, onMapReady]);

  useEffect(() => {
    // Wait for container ref to be set and Leaflet to be ready
    const timer = setTimeout(() => {
      initializeMap();
    }, 100); // Increase delay to ensure Leaflet is loaded

    return () => {
      clearTimeout(timer);
      if (mapRef.current) {
        try {
          mapRef.current.remove();
        } catch (error) {
          console.error('Error removing map:', error);
        }
        mapRef.current = null;
      }
    };
  }, [initializeMap]);

  return mapRef;
}
