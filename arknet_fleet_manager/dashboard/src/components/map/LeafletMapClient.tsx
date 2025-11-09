"use client";
import React from "react";
import MapControlPanel from "./MapControlPanel";

type Props = {
  center?: [number, number];
  zoom?: number;
  height?: string;
};

type LeafletMapType = {
  remove: () => void;
  invalidateSize: () => void;
};

type LeafletStatic = {
  map: (el: HTMLElement, opts?: Record<string, unknown>) => LeafletMapType;
  tileLayer: (url: string, opts?: Record<string, unknown>) => { addTo: (m: LeafletMapType) => void };
  control: { 
    scale: (opts?: Record<string, unknown>) => { addTo: (m: LeafletMapType) => void } 
  };
};

function ensureLeafletLoaded(): Promise<void> {
  // If already available, resolve immediately
  if (typeof window !== "undefined" && (window as unknown as { L?: LeafletStatic }).L) return Promise.resolve();

  return new Promise((resolve, reject) => {
    // Inject CSS
    if (!document.querySelector('link[data-leaflet]')) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
      link.setAttribute('data-leaflet', '1');
      document.head.appendChild(link);
    }

    // Inject script
    if (!document.querySelector('script[data-leaflet]')) {
      const s = document.createElement('script');
      s.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
      s.async = true;
      s.setAttribute('data-leaflet', '1');
      s.onload = () => resolve();
      s.onerror = (e) => reject(e);
      document.body.appendChild(s);
    } else {
      // script already present but library may not be ready; poll
      const waitFor = () => {
        if ((window as unknown as { L?: LeafletStatic }).L) resolve();
        else setTimeout(waitFor, 50);
      };
      waitFor();
    }
  });
}

export default function LeafletMapClient({ center = [13.2, -59.55], zoom = 10, height = '60vh' }: Props) {
  const ref = React.useRef<HTMLDivElement | null>(null);
  const mapRef = React.useRef<LeafletMapType | null>(null);
  const [panelOpen, setPanelOpen] = React.useState(false);
  const [showRoutePoints, setShowRoutePoints] = React.useState(false);

  React.useEffect(() => {
    let mounted = true;
    ensureLeafletLoaded()
      .then(() => {
        if (!mounted) return;
  const L = (window as unknown as { L?: LeafletStatic }).L as LeafletStatic;
        if (!ref.current) return;
        // avoid re-init
        if (mapRef.current) return;

        const map = L.map(ref.current, {
          center,
          zoom,
          minZoom: 5,
          maxZoom: 18,
          zoomControl: true,
        });

        // Use Carto Voyager tiles for a clean, Google-like look
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; OpenStreetMap contributors',
          maxZoom: 19,
        }).addTo(map);

        // PERMANENTLY visible scale - force it to stay on screen
        L.control.scale({ 
          position: 'bottomleft', 
          imperial: true, 
          metric: true,
          maxWidth: 150
        }).addTo(map);
        
        // Force the scale element to always display using direct DOM manipulation
        const forceScaleVisible = () => {
          const scaleElement = ref.current?.querySelector('.leaflet-control-scale');
          if (scaleElement) {
            (scaleElement as HTMLElement).style.display = 'block';
            (scaleElement as HTMLElement).style.visibility = 'visible';
            (scaleElement as HTMLElement).style.opacity = '1';
          }
        };
        
        // Apply immediately and on every zoom/move
        setTimeout(forceScaleVisible, 200);
        (map as unknown as { on: (event: string, fn: () => void) => void }).on('zoomend', forceScaleVisible);
        (map as unknown as { on: (event: string, fn: () => void) => void }).on('moveend', forceScaleVisible);

        mapRef.current = map;
      })
      .catch(() => {
        // ignore load errors for now
      });

    return () => {
      mounted = false;
      if (mapRef.current) {
        try { mapRef.current.remove(); } catch { /* ignore */ }
        mapRef.current = null;
      }
    };
  }, [center, zoom]);

  // When showRoutePoints toggles we could add/remove markers here.
  React.useEffect(() => {
    if (!mapRef.current) return;
    // placeholder: future implementation will add/remove POI markers for routes
    // For now just log to console so developers see the change
    console.log('showRoutePoints ->', showRoutePoints);
  }, [showRoutePoints]);

  return (
    <div style={{ position: 'relative', width: '100%', height }}>
      {/* map container */}
      <div ref={ref} style={{ width: '100%', height }} />

      {/* hamburger button */}
      <div style={{ position: 'absolute', top: 12, left: 12, zIndex: 1000001 }}>
        <button
          aria-label="Open map controls"
          onClick={() => setPanelOpen((v) => !v)}
          style={{
            width: 44,
            height: 44,
            borderRadius: 8,
            background: 'rgba(255,255,255,0.95)',
            boxShadow: '0 6px 18px rgba(0,0,0,0.18)',
            border: 'none',
            cursor: 'pointer'
          }}
        >
          <svg width="20" height="14" viewBox="0 0 20 14" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="20" height="2" rx="1" fill="#111" />
            <rect y="6" width="20" height="2" rx="1" fill="#111" />
            <rect y="12" width="20" height="2" rx="1" fill="#111" />
          </svg>
        </button>
      </div>

      {/* Map control panel (slide-in) - lazy import component to keep bundle light */}
      {typeof window !== 'undefined' && (
        <MapControlPanel
          open={panelOpen}
          onClose={() => setPanelOpen(false)}
          showRoutePoints={showRoutePoints}
          setShowRoutePoints={setShowRoutePoints}
        />
      )}
    </div>
  );
}
