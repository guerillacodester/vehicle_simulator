"use client";
import React, { useRef, useState, useCallback, useEffect } from "react";
import MapControlPanel from "./MapControlPanel";
import { MapErrorBoundary } from "./MapErrorBoundary";
import { useTransitProvider } from '../../lib/transitProvider';
import { useLeafletLoader } from './useLeafletLoader';
import { useLeafletMap } from './useLeafletMap';
import { usePOILayer } from './usePOILayer';
import type { RouteDetail } from '@transit/types';

type Props = {
  center?: [number, number];
  zoom?: number;
  height?: string;
};

/**
 * Main Leaflet map component with control panel
 * Manages map state, POI markers, and user interactions
 */
export default function LeafletMapClient({ center, zoom, height = '60vh' }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [showRoutePoints, setShowRoutePoints] = useState(false);
  const [selectedRouteId, setSelectedRouteId] = useState<string | null>(null);
  const [fetchedRouteDetails, setFetchedRouteDetails] = useState<RouteDetail | null>(null);
  
  const provider = useTransitProvider();
  const { loading: leafletLoading } = useLeafletLoader();
  
  // Debug: Log component render state
  useEffect(() => {
    console.log('[LeafletMapClient] Component rendered', {
      leafletLoading,
      containerExists: !!containerRef.current,
      height
    });
  }, [leafletLoading, height]);
  
  // Derive route details - clear if no route selected
  const routeDetails = selectedRouteId ? fetchedRouteDetails : null;
  
  // Initialize map
  const mapRef = useLeafletMap({
    containerRef: containerRef as React.RefObject<HTMLDivElement>,
    center,
    zoom,
  });
  
  // Manage POI layer
  usePOILayer({
    mapRef,
    showPOIs: showRoutePoints,
    routeDetails,
  });

  // Fetch route details when route is selected
  useEffect(() => {
    if (!selectedRouteId) {
      return;
    }

    let cancelled = false;

    provider
      .getRouteDetails(selectedRouteId)
      .then((details) => {
        if (!cancelled) {
          setFetchedRouteDetails(details || null);
        }
      })
      .catch((error) => {
        console.error('Failed to fetch route details:', error);
        if (!cancelled) {
          setFetchedRouteDetails(null);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [selectedRouteId, provider]);

  // Handle route selection from control panel
  const handleSelectRoute = useCallback((routeId: string) => {
    setSelectedRouteId(routeId);
    if (!showRoutePoints) {
      setShowRoutePoints(true);
    }
    setPanelOpen(true);
  }, [showRoutePoints]);

  // Force render after timeout even if Leaflet hasn't loaded
  const [forceRender, setForceRender] = useState(false);
  useEffect(() => {
    const timeout = setTimeout(() => {
      console.warn('[LeafletMapClient] Forcing render after 5s timeout');
      setForceRender(true);
    }, 5000);
    return () => clearTimeout(timeout);
  }, []);

  if (leafletLoading && !forceRender) {
    return (
      <div style={{ width: '100%', height, display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--background)' }}>
        <div>Loading map...</div>
      </div>
    );
  }

  return (
    <div style={{ position: 'relative', width: '100%', height, overflow: 'hidden' }}>
      {/* map container - ALWAYS render first, independent of any API calls */}
      <div 
        ref={containerRef} 
        id="leaflet-map-container"
        style={{ 
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          width: '100%', 
          height: '100%',
          background: '#e0e0e0',
          minHeight: '400px',
          zIndex: 0
        }} 
      />

      {/* Navigation drawer toggle - ALWAYS render, independent of API */}
      <button
        className={`map-hamburger ${panelOpen ? 'open' : ''}`}
        onClick={() => setPanelOpen((v) => !v)}
        aria-label={panelOpen ? 'Close navigation' : 'Open navigation'}
        aria-expanded={panelOpen}
        aria-controls="map-nav-drawer"
      >
        <div className="map-hamburger-icon">
          <span />
          <span />
          <span />
        </div>
      </button>

      {/* Navigation drawer - wrapped to catch any errors and prevent map from breaking */}
      {typeof window !== 'undefined' && (
        <MapErrorBoundary>
          <MapControlPanel
            open={panelOpen}
            onClose={() => setPanelOpen(false)}
            showRoutePoints={showRoutePoints}
            setShowRoutePoints={setShowRoutePoints}
            onSelectRoute={handleSelectRoute}
          />
        </MapErrorBoundary>
      )}
    </div>
  );
}
