import { useEffect, useRef } from 'react';
import type { LeafletMap, LeafletLayerGroup } from './leafletTypes';
import { getLeafletGlobal } from './useLeafletLoader';
import type { RouteDetail } from '@transit/types';

interface UsePOILayerOptions {
  mapRef: React.RefObject<LeafletMap | null>;
  showPOIs: boolean;
  routeDetails: RouteDetail | null;
}

/**
 * Custom hook to manage POI (Point of Interest) markers on the map
 * Handles adding/removing stop markers and fitting map bounds
 */
export function usePOILayer({ mapRef, showPOIs, routeDetails }: UsePOILayerOptions) {
  const layerGroupRef = useRef<LeafletLayerGroup | null>(null);

  // Initialize layer group
  useEffect(() => {
    const L = getLeafletGlobal();
    const map = mapRef.current;
    if (!L || !map || layerGroupRef.current) return;

    try {
      const layerGroup = L.layerGroup();
      layerGroup.addTo(map);
      layerGroupRef.current = layerGroup;
    } catch (error) {
      console.error('Failed to create POI layer group:', error);
    }

    return () => {
      if (layerGroupRef.current) {
        try {
          layerGroupRef.current.remove();
        } catch (error) {
          console.error('Error removing POI layer:', error);
        }
        layerGroupRef.current = null;
      }
    };
  }, [mapRef]);

  // Update markers when showPOIs or routeDetails changes
  useEffect(() => {
    const L = getLeafletGlobal();
    const layerGroup = layerGroupRef.current;
    const map = mapRef.current;
    
    if (!L || !layerGroup || !map) return;

    // Clear existing markers
    try {
      layerGroup.clearLayers();
    } catch (error) {
      console.error('Error clearing layers:', error);
      return;
    }

    // If POIs are disabled or no route selected, stop here
    if (!showPOIs || !routeDetails) return;

    const stops = routeDetails.stops || [];
    if (stops.length === 0) return;

    try {
      // Add markers for each stop
      const markers = stops.map((stop) => {
        const marker = L.marker([stop.lat, stop.lon]);
        marker.bindPopup(`<strong>${stop.name}</strong>`);
        layerGroup.addLayer(marker);
        return marker;
      });

      // Fit map to show all markers
      if (markers.length > 0) {
        const bounds = layerGroup.getBounds();
        if (bounds) {
          map.fitBounds(bounds.pad(0.1));
        }
      }
    } catch (error) {
      console.error('Error adding POI markers:', error);
    }
  }, [mapRef, showPOIs, routeDetails]);

  return layerGroupRef;
}
