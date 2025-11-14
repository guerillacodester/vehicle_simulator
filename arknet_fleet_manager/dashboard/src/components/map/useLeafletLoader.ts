import { useEffect, useState } from 'react';
import type { LeafletStatic } from './leafletTypes';

const LEAFLET_CDN_CSS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
const LEAFLET_CDN_JS = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';

/**
 * Ensures Leaflet library is loaded from CDN
 * Returns loading state and any errors
 */
export function useLeafletLoader() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    console.log('[useLeafletLoader] Starting...');
    
    // Check if already loaded
    if (typeof window === 'undefined') {
      console.log('[useLeafletLoader] Window is undefined (SSR)');
      return;
    }
    
    const checkLoaded = () => {
      if ('L' in window) {
        console.log('[useLeafletLoader] Leaflet already loaded!');
        setLoading(false);
        return true;
      }
      return false;
    };

    if (checkLoaded()) return;

    // Inject CSS
    if (!document.querySelector(`link[href="${LEAFLET_CDN_CSS}"]`)) {
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = LEAFLET_CDN_CSS;
      link.setAttribute('data-leaflet-css', 'true');
      document.head.appendChild(link);
    }

    // Inject JS
    if (!document.querySelector(`script[src="${LEAFLET_CDN_JS}"]`)) {
      const script = document.createElement('script');
      script.src = LEAFLET_CDN_JS;
      script.async = true;
      script.setAttribute('data-leaflet-js', 'true');
      
      script.onload = () => {
        console.log('[useLeafletLoader] Leaflet script loaded successfully!');
        setLoading(false);
      };
      
      script.onerror = () => {
        console.error('[useLeafletLoader] Failed to load Leaflet script!');
        setError(new Error('Failed to load Leaflet library'));
        setLoading(false);
      };
      
      document.body.appendChild(script);
    } else {
      // Script tag exists, poll for library
      const pollInterval = setInterval(() => {
        if (checkLoaded()) {
          clearInterval(pollInterval);
        }
      }, 50);
      
      return () => clearInterval(pollInterval);
    }
  }, []);

  return { loading, error };
}

/**
 * Get Leaflet global safely
 */
export function getLeafletGlobal(): LeafletStatic | null {
  if (typeof window === 'undefined') return null;
  if (!('L' in window)) return null;
  return (window as unknown as { L: LeafletStatic }).L;
}
