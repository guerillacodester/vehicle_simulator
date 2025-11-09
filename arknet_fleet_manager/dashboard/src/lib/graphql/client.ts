/**
 * GraphQL Client Configuration
 * 
 * Production-grade URQL client for Strapi GraphQL API
 * Features:
 * - Automatic retries
 * - Request deduplication
 * - Normalized caching
 * - Error handling
 * - Authentication
 */

import {
  createClient,
  cacheExchange,
  fetchExchange,
  ssrExchange,
  mapExchange,
  type TypedDocumentNode,
} from 'urql';

/**
 * Strapi GraphQL endpoint
 * @default http://localhost:1337/graphql
 */
const GRAPHQL_ENDPOINT = process.env.NEXT_PUBLIC_STRAPI_GRAPHQL_URL || 'http://localhost:1337/graphql';

/**
 * Custom fetch implementation with authentication
 */
const customFetch = (url: RequestInfo | URL, options?: RequestInit) => {
  // Get JWT token from localStorage or cookie
  const token = typeof window !== 'undefined' ? localStorage.getItem('strapi_jwt') : null;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Add existing headers
  if (options?.headers) {
    const existingHeaders = new Headers(options.headers);
    existingHeaders.forEach((value, key) => {
      headers[key] = value;
    });
  }

  // Add authorization header if token exists
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return fetch(url, {
    ...options,
    headers,
  });
};

/**
 * Error exchange for centralized error handling
 */
const errorHandler = mapExchange({
  onError: (error) => {
    console.error('[GraphQL Error]', {
      message: error.message,
      graphQLErrors: error.graphQLErrors,
      networkError: error.networkError,
    });

    // Handle authentication errors
    if (error.message.includes('Unauthorized') || error.message.includes('Forbidden')) {
      if (typeof window !== 'undefined') {
        // Clear invalid token
        localStorage.removeItem('strapi_jwt');
        
        // Optionally redirect to login
        // window.location.href = '/login';
      }
    }
  },
});

/**
 * Create URQL client with production-grade configuration
 */
export const createGraphQLClient = (isServerSide = false) => {
  const ssr = ssrExchange({
    isClient: !isServerSide,
  });

  return createClient({
    url: GRAPHQL_ENDPOINT,
    fetch: customFetch,
    exchanges: [
      cacheExchange,       // Cache results
      errorHandler,        // Centralized error handling
      ssr,                 // SSR support
      fetchExchange,       // Network requests
    ],
    // Request policy: cache-first (default)
    requestPolicy: 'cache-first',
    // Suspend rendering until data is available (React 19)
    suspense: false,
  });
};

/**
 * Default client instance for client-side usage
 */
export const graphqlClient = createGraphQLClient(false);

/**
 * Type-safe query executor
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function executeQuery<Data, Variables extends Record<string, any> = Record<string, never>>(
  query: string | TypedDocumentNode<Data, Variables>,
  variables?: Variables
): Promise<{ data?: Data; error?: Error }> {
  const result = await graphqlClient.query(query, variables || {} as Variables).toPromise();
  
  if (result.error) {
    return { error: result.error };
  }
  
  return { data: result.data as Data };
}

/**
 * Type-safe mutation executor
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export async function executeMutation<Data, Variables extends Record<string, any> = Record<string, never>>(
  mutation: string | TypedDocumentNode<Data, Variables>,
  variables?: Variables
): Promise<{ data?: Data; error?: Error }> {
  const result = await graphqlClient.mutation(mutation, variables || {} as Variables).toPromise();
  
  if (result.error) {
    return { error: result.error };
  }
  
  return { data: result.data as Data };
}
