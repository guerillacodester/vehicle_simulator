/**
 * GraphQL Provider
 * 
 * Wraps the application with URQL Provider and React Query
 * for production-grade GraphQL + caching
 */

'use client';

import { Provider as UrqlProvider } from 'urql';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { graphqlClient } from './client';
import { type ReactNode, useState } from 'react';

interface GraphQLProviderProps {
  children: ReactNode;
}

/**
 * GraphQL Provider Component
 * 
 * Provides both URQL (GraphQL) and React Query (caching) contexts
 * to the application
 */
export function GraphQLProvider({ children }: GraphQLProviderProps) {
  // Create React Query client with production-grade defaults
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Stale time: 5 minutes
            staleTime: 5 * 60 * 1000,
            // Cache time: 10 minutes
            gcTime: 10 * 60 * 1000,
            // Retry failed requests up to 3 times
            retry: 3,
            // Retry delay with exponential backoff
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
            // Refetch on window focus in production
            refetchOnWindowFocus: process.env.NODE_ENV === 'production',
            // Don't refetch on mount if data is fresh
            refetchOnMount: false,
          },
          mutations: {
            // Retry mutations once
            retry: 1,
          },
        },
      })
  );

  return (
    <UrqlProvider value={graphqlClient}>
      <QueryClientProvider client={queryClient}>
        {children}
        {/* Show React Query DevTools in development */}
        {process.env.NODE_ENV === 'development' && (
          <ReactQueryDevtools initialIsOpen={false} />
        )}
      </QueryClientProvider>
    </UrqlProvider>
  );
}
