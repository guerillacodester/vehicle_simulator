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
  const initializingRef = useRef(false);

  useEffect(() => {
    // Prevent multiple initializations
    if (initializingRef.current || mapRef.current) {
      return;
    }

    // Poll for both Leaflet AND container to be ready
    const pollInterval = setInterval(() => {
      if (!containerRef.current) {
        console.log('[useLeafletMap] Waiting for container...');
        return;
      }

      const L = getLeafletGlobal();
      if (!L) {
        console.log('[useLeafletMap] Waiting for Leaflet to load...');
        return;
      }

      // Both container and Leaflet are ready
      clearInterval(pollInterval);
      
      if (initializingRef.current || mapRef.current) {
        return;
      }

      initializingRef.current = true;

      try {
        console.log('[useLeafletMap] Creating Leaflet map...');
        const map = L.map(containerRef.current, {
          center,
          zoom,
          minZoom: MAP_CONFIG.MIN_ZOOM,
          maxZoom: MAP_CONFIG.MAX_ZOOM,
          zoomControl: false,
        });
        
        L.control.zoom({
          position: 'bottomright'
        }).addTo(map);

        L.tileLayer(MAP_CONFIG.TILE_URL, {
          attribution: MAP_CONFIG.ATTRIBUTION,
          maxZoom: MAP_CONFIG.TILE_MAX_ZOOM,
        }).addTo(map);

        L.control.scale({
          position: 'topright',
          imperial: true,
          metric: true,
          maxWidth: 150,
        }).addTo(map);

        mapRef.current = map;
        console.log('[useLeafletMap] Map created successfully!');
        onMapReady?.(map);
      } catch (error) {
        console.error('[useLeafletMap] Failed to initialize map:', error);
        initializingRef.current = false;
      }
    }, 100);

    return () => {
      clearInterval(pollInterval);
      if (mapRef.current) {
        try {
          mapRef.current.remove();
        } catch (error) {
          console.error('Error removing map:', error);
        }
        mapRef.current = null;
        initializingRef.current = false;
      }
    };
  }, []);

  return mapRef;
}
