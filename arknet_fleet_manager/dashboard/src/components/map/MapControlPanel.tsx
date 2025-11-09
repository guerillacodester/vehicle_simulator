"use client";
import React from "react";
import RouteSearch from "../transit/RouteSearch";

type Props = {
  open: boolean;
  onClose: () => void;
  showRoutePoints: boolean;
  setShowRoutePoints: (v: boolean) => void;
  // future callbacks: show/hide polylines, focus on vehicle, etc.
};

export default function MapControlPanel({ open, onClose, showRoutePoints, setShowRoutePoints }: Props) {
  return (
    <aside
      className={`map-control-panel ${open ? 'open' : ''}`}
      aria-hidden={!open}
      style={{
        position: 'absolute',
        top: 12,
        left: 12,
        width: 320,
        maxWidth: 'calc(100% - 48px)',
        height: 'calc(100% - 24px)',
        background: 'rgba(255,255,255,0.98)',
        boxShadow: '0 8px 24px rgba(0,0,0,0.25)',
        borderRadius: 8,
        transform: 'translateX(-8px)',
        transition: 'transform 240ms ease, opacity 240ms ease',
        overflow: 'auto',
        zIndex: 1000000,
        padding: 8,
        display: open ? 'block' : 'none'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '6px 8px' }}>
        <strong>Map Controls</strong>
        <div>
          <button onClick={onClose} title="Close" style={{ padding: 6, borderRadius: 6 }}>
            ✕
          </button>
        </div>
      </div>

      <div style={{ padding: 8 }}>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <input
            type="checkbox"
            checked={showRoutePoints}
            onChange={(e) => setShowRoutePoints(e.target.checked)}
          />
          <span>Show route POIs (stops)</span>
        </label>

        <div style={{ marginBottom: 12 }}>
          <small style={{ color: '#666' }}>Search routes or vehicle ids</small>
          <div style={{ marginTop: 6 }}>
            <RouteSearch />
          </div>
        </div>

        <section style={{ marginTop: 8 }}>
          <h4 style={{ marginBottom: 6 }}>Quick toggles</h4>
          <div style={{ display: 'grid', gap: 6 }}>
            <button style={{ padding: 8, borderRadius: 6 }}>Fit to selected route</button>
            <button style={{ padding: 8, borderRadius: 6 }}>Center on my location</button>
          </div>
        </section>
      </div>
    </aside>
  );
}
