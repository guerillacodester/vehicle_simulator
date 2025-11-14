/**
 * Route Hooks
 * 
 * Custom React hooks for route queries and mutations
 * Provides type-safe, easy-to-use interface for components
 */

'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { executeQuery, executeMutation } from '../lib/graphql/client';
import {
  GET_ROUTES_QUERY,
  GET_ROUTE_QUERY,
  GET_ROUTE_BY_CODE_QUERY,
  SEARCH_ROUTES_QUERY,
  type GetRoutesQueryVariables,
  type GetRoutesQueryResult,
  type GetRouteQueryVariables,
  type GetRouteQueryResult,
  type SearchRoutesQueryVariables,
  type SearchRoutesQueryResult,
} from '../lib/graphql/queries/routes';
import {
  CREATE_ROUTE_MUTATION,
  UPDATE_ROUTE_MUTATION,
  DELETE_ROUTE_MUTATION,
  type CreateRouteMutationVariables,
  type CreateRouteMutationResult,
  type UpdateRouteMutationVariables,
  type UpdateRouteMutationResult,
  type DeleteRouteMutationVariables,
  type DeleteRouteMutationResult,
  type RouteInput,
} from '../lib/graphql/mutations/routes';

/**
 * Hook to fetch all routes with pagination
 * 
 * @example
 * ```tsx
 * const { data, loading, error, refetch } = useRoutes({ limit: 20 });
 * ```
 */
export function useRoutes(variables?: GetRoutesQueryVariables) {
  return useQuery({
    queryKey: ['routes', variables],
    queryFn: async () => {
      const { data, error } = await executeQuery<GetRoutesQueryResult, GetRoutesQueryVariables>(
        GET_ROUTES_QUERY,
        variables
      );
      if (error) throw error;
      return data!.routes;
    },
  });
}

/**
 * Hook to fetch a single route by ID
 * 
 * @example
 * ```tsx
 * const { data: route, loading } = useRoute({ id: '14' });
 * ```
 */
export function useRoute(variables: GetRouteQueryVariables) {
  return useQuery({
    queryKey: ['route', variables.documentId],
    queryFn: async () => {
      const { data, error } = await executeQuery<GetRouteQueryResult, GetRouteQueryVariables>(
        GET_ROUTE_QUERY,
        variables
      );
      if (error) throw error;
      return data!.route;
    },
    enabled: !!variables.documentId,
  });
}

/**
 * Hook to fetch route by short_name (route code)
 * 
 * @example
 * ```tsx
 * const { data: route } = useRouteByCode({ shortName: '1' });
 * ```
 */
export function useRouteByCode(shortName: string) {
  return useQuery({
    queryKey: ['route', 'code', shortName],
    queryFn: async () => {
      const { data, error } = await executeQuery<SearchRoutesQueryResult, { shortName: string }>(
        GET_ROUTE_BY_CODE_QUERY,
        { shortName }
      );
      if (error) throw error;
      return data!.routes[0];
    },
    enabled: !!shortName,
  });
}

/**
 * Hook to search routes by name
 * 
 * @example
 * ```tsx
 * const { data: routes } = useSearchRoutes('Airport', { limit: 5 });
 * ```
 */
export function useSearchRoutes(search: string, options?: { limit?: number }) {
  return useQuery({
    queryKey: ['routes', 'search', search, options?.limit],
    queryFn: async () => {
      const { data, error } = await executeQuery<SearchRoutesQueryResult, SearchRoutesQueryVariables>(
        SEARCH_ROUTES_QUERY,
        { search, limit: options?.limit }
      );
      if (error) throw error;
      return data!.routes;
    },
    enabled: search.length >= 2, // Only search when at least 2 characters
  });
}

/**
 * Hook to create a new route
 * 
 * @example
 * ```tsx
 * const { mutate: createRoute, isPending } = useCreateRoute();
 * 
 * createRoute({
 *   short_name: '2',
 *   long_name: 'Route 2 - City Center'
 * });
 * ```
 */
export function useCreateRoute() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (input: RouteInput) => {
      const { data, error } = await executeMutation<CreateRouteMutationResult, CreateRouteMutationVariables>(
        CREATE_ROUTE_MUTATION,
        { data: input }
      );
      if (error) throw error;
      return data!.createRoute;
    },
    onSuccess: () => {
      // Invalidate routes list to trigger refetch
      queryClient.invalidateQueries({ queryKey: ['routes'] });
    },
  });
}

/**
 * Hook to update an existing route
 * 
 * @example
 * ```tsx
 * const { mutate: updateRoute } = useUpdateRoute();
 * 
 * updateRoute({
 *   id: '14',
 *   data: { long_name: 'Updated Route Name' }
 * });
 * ```
 */
export function useUpdateRoute() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId, data }: { documentId: string; data: Partial<RouteInput> }) => {
      const { data: result, error } = await executeMutation<UpdateRouteMutationResult, UpdateRouteMutationVariables>(
        UPDATE_ROUTE_MUTATION,
        { documentId, data }
      );
      if (error) throw error;
      return result!.updateRoute;
    },
    onSuccess: (data) => {
      // Invalidate both list and specific route
      queryClient.invalidateQueries({ queryKey: ['routes'] });
      queryClient.invalidateQueries({ queryKey: ['route', data.documentId] });
    },
  });
}

/**
 * Hook to delete a route
 * 
 * @example
 * ```tsx
 * const { mutate: deleteRoute } = useDeleteRoute();
 * 
 * deleteRoute({ id: '14' });
 * ```
 */
export function useDeleteRoute() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ documentId }: { documentId: string }) => {
      const { data, error } = await executeMutation<DeleteRouteMutationResult, DeleteRouteMutationVariables>(
        DELETE_ROUTE_MUTATION,
        { documentId }
      );
      if (error) throw error;
      return data!.deleteRoute.documentId;
    },
    onSuccess: (data) => {
      // Invalidate both list and specific route
      queryClient.invalidateQueries({ queryKey: ['routes'] });
      queryClient.invalidateQueries({ queryKey: ['route', data] });
    },
  });
}

/**
 * Hook to refetch routes manually
 * 
 * @example
 * ```tsx
 * const refetchRoutes = useRefetchRoutes();
 * 
 * <button onClick={() => refetchRoutes()}>Refresh</button>
 * ```
 */
export function useRefetchRoutes() {
  const queryClient = useQueryClient();

  return () => {
    queryClient.invalidateQueries({ queryKey: ['routes'] });
  };
}
