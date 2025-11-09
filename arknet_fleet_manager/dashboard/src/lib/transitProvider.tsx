import React from 'react';
import { TransitDataProvider } from '@transit/TransitDataProvider';

// Create a singleton provider for easy reuse in the dashboard
const provider = new TransitDataProvider({
  baseUrl: process.env.NEXT_PUBLIC_TRANSIT_BASE_URL || 'http://localhost:4001',
  wsUrl: process.env.NEXT_PUBLIC_TRANSIT_WS_URL || 'ws://localhost:4001'
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
