"use client";
import React, { useEffect, useRef, useState } from "react";
import RouteSearch from "../transit/RouteSearch";

type Props = {
  open: boolean;
  onClose: () => void;
  showRoutePoints: boolean;
  setShowRoutePoints: (v: boolean) => void;
  onSelectRoute?: (routeId: string) => void;
};

export default function MapControlPanel({ open, onClose, showRoutePoints, setShowRoutePoints, onSelectRoute }: Props) {
  const drawerRef = useRef<HTMLElement>(null);
  const closeButtonRef = useRef<HTMLButtonElement>(null);
  const [isPinned, setIsPinned] = useState(false);

  // Focus management - trap focus inside drawer when open
  useEffect(() => {
    if (!open) return;

    // Focus close button when drawer opens
    closeButtonRef.current?.focus();

    // Handle Escape key
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    // Trap focus inside drawer
    const handleTab = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;
      
      const focusableElements = drawerRef.current?.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      
      if (!focusableElements || focusableElements.length === 0) return;
      
      const firstElement = focusableElements[0] as HTMLElement;
      const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          lastElement.focus();
          e.preventDefault();
        }
      } else {
        if (document.activeElement === lastElement) {
          firstElement.focus();
          e.preventDefault();
        }
      }
    };

    document.addEventListener('keydown', handleEscape);
    document.addEventListener('keydown', handleTab);

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.removeEventListener('keydown', handleTab);
    };
  }, [open, onClose]);

  // Prevent body scroll only when drawer is open AND unpinned (modal behavior)
  useEffect(() => {
    // Only block scroll in modal mode (unpinned)
    const shouldBlockScroll = open && !isPinned;
    
    if (shouldBlockScroll) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [open, isPinned]);

  return (
    <>
      {/* Overlay/Backdrop - only show when NOT pinned */}
      <div 
        className={`map-overlay ${open && !isPinned ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
        role="presentation"
      />
      
      {/* Navigation Drawer */}
      <aside 
        ref={drawerRef}
        id="map-nav-drawer"
        className={`map-control-panel ${open ? 'open' : ''} ${isPinned ? 'pinned' : ''}`}
        aria-hidden={!open}
        role="navigation"
        aria-label="Map controls"
      >
        <div className="map-control-header">
          <h3 id="drawer-title">Map Controls</h3>
          <div className="map-control-header-actions">
            <button 
              onClick={() => setIsPinned(!isPinned)}
              className="map-control-pin"
              aria-label={isPinned ? 'Unpin panel' : 'Pin panel'}
              title={isPinned ? 'Unpin panel' : 'Pin panel'}
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                {isPinned ? (
                  // Pinned icon (filled pin)
                  <path d="M10 2L8 6H5L7 9V14L9 16V19H11V16L13 14V9L15 6H12L10 2Z" fill="currentColor" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                ) : (
                  // Unpinned icon (outline pin)
                  <path d="M10 2L8 6H5L7 9V14L9 16V19H11V16L13 14V9L15 6H12L10 2Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                )}
              </svg>
            </button>
            <button 
              ref={closeButtonRef}
              onClick={onClose} 
              className="map-control-close"
              aria-label="Close navigation drawer"
            >
              <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </button>
          </div>
        </div>

        <div className="map-control-body">
          <label className="map-control-row">
            <input
              type="checkbox"
              checked={showRoutePoints}
              onChange={(e) => setShowRoutePoints(e.target.checked)}
              id="toggle-pois"
            />
            <span>Show route POIs (stops)</span>
          </label>

          <div className="map-control-section">
            <h4>Search Routes</h4>
            <div className="map-control-search">
              <RouteSearch onSelectRoute={(r) => onSelectRoute?.(r.id)} />
            </div>
          </div>

          <section className="map-control-section">
            <h4>Quick Actions</h4>
            <div className="map-control-quick">
              <button className="btn" type="button">Fit to selected route</button>
              <button className="btn" type="button">Center on my location</button>
            </div>
          </section>
        </div>
      </aside>
    </>
  );
}
