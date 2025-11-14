import React from 'react';
import { TransitDataProvider } from '@transit/TransitDataProvider';

// Create a singleton provider for easy reuse in the dashboard
// Connects to Strapi backend API
const provider = new TransitDataProvider({
  baseUrl: process.env.NEXT_PUBLIC_STRAPI_URL || 'http://localhost:1337/api',
  wsUrl: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:1337'
});

export function getTransitProvider() {
  return provider;
}

// Small React hook to access the provider in components/pages
export function useTransitProvider() {
  // The provider is a stable singleton and does not need to be stored in a ref.
  // Return it directly or memoize for consistency in render cycles.
  // Keep the hook so callers can switch to a context-based implementation later.
  return React.useMemo(() => provider, []);
}
