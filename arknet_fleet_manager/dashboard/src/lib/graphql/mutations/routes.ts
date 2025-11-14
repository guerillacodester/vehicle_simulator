/**
 * Route Mutations
 * 
 * GraphQL mutations for creating, updating, and deleting routes in Strapi
 */

import { gql } from 'urql';
import { ROUTE_BASIC_FRAGMENT } from '../queries/routes';
import type { Route } from '../queries/routes';

/**
 * Create a new route
 * 
 * ⚠️ NOTE: Route geometry should be managed separately via GeoJSON files
 * See ROUTE_GEOMETRY_BIBLE.md
 */
export const CREATE_ROUTE_MUTATION = gql`
  ${ROUTE_BASIC_FRAGMENT}
  
  mutation CreateRoute($data: RouteInput!) {
    createRoute(data: $data) {
      ...RouteBasic
    }
  }
`;

/**
 * Update an existing route
 */
export const UPDATE_ROUTE_MUTATION = gql`
  ${ROUTE_BASIC_FRAGMENT}
  
  mutation UpdateRoute($documentId: ID!, $data: RouteInput!) {
    updateRoute(documentId: $documentId, data: $data) {
      ...RouteBasic
    }
  }
`;

/**
 * Delete a route
 */
export const DELETE_ROUTE_MUTATION = gql`
  mutation DeleteRoute($documentId: ID!) {
    deleteRoute(documentId: $documentId) {
      documentId
    }
  }
`;

/**
 * TypeScript types for route mutations
 */

export interface RouteInput {
  short_name: string;
  long_name: string;
  description?: string;
  color?: string;
  text_color?: string;
  route_type?: string;
}

export interface CreateRouteMutationVariables {
  data: RouteInput;
}

export interface CreateRouteMutationResult {
  createRoute: Route;
}

export interface UpdateRouteMutationVariables {
  documentId: string;
  data: Partial<RouteInput>;
}

export interface UpdateRouteMutationResult {
  updateRoute: Route;
}

export interface DeleteRouteMutationVariables {
  documentId: string;
}

export interface DeleteRouteMutationResult {
  deleteRoute: {
    documentId: string;
  };
}
