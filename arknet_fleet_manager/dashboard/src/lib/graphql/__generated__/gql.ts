/* eslint-disable */
import * as types from './graphql';
import { TypedDocumentNode as DocumentNode } from '@graphql-typed-document-node/core';

/**
 * Map of all GraphQL operations in the project.
 *
 * This map has several performance disadvantages:
 * 1. It is not tree-shakeable, so it will include all operations in the project.
 * 2. It is not minifiable, so the string of a GraphQL query will be multiple times inside the bundle.
 * 3. It does not support dead code elimination, so it will add unused operations.
 *
 * Therefore it is highly recommended to use the babel or swc plugin for production.
 * Learn more about it here: https://the-guild.dev/graphql/codegen/plugins/presets/preset-client#reducing-bundle-size
 */
type Documents = {
    "\n  \n  \n  mutation CreateRoute($data: RouteInput!) {\n    createRoute(data: $data) {\n      ...RouteBasic\n    }\n  }\n": typeof types.CreateRouteDocument,
    "\n  \n  \n  mutation UpdateRoute($documentId: ID!, $data: RouteInput!) {\n    updateRoute(documentId: $documentId, data: $data) {\n      ...RouteBasic\n    }\n  }\n": typeof types.UpdateRouteDocument,
    "\n  mutation DeleteRoute($documentId: ID!) {\n    deleteRoute(documentId: $documentId) {\n      documentId\n    }\n  }\n": typeof types.DeleteRouteDocument,
    "\n  fragment RouteBasic on Route {\n    documentId\n    short_name\n    long_name\n    description\n    color\n    route_type\n  }\n": typeof types.RouteBasicFragmentDoc,
    "\n  \n  \n  query GetRoutes($limit: Int, $start: Int, $sort: [String]) {\n    routes(\n      pagination: { limit: $limit, start: $start }\n      sort: $sort\n    ) {\n      ...RouteBasic\n    }\n  }\n": typeof types.GetRoutesDocument,
    "\n  \n  \n  query GetRoute($documentId: ID!) {\n    route(documentId: $documentId) {\n      ...RouteBasic\n      createdAt\n      updatedAt\n    }\n  }\n": typeof types.GetRouteDocument,
    "\n  \n  \n  query GetRouteByCode($shortName: String!) {\n    routes(filters: { short_name: { eq: $shortName } }) {\n      ...RouteBasic\n    }\n  }\n": typeof types.GetRouteByCodeDocument,
    "\n  \n  \n  query SearchRoutes($search: String!, $limit: Int = 10) {\n    routes(\n      filters: {\n        or: [\n          { short_name: { containsi: $search } }\n          { long_name: { containsi: $search } }\n        ]\n      }\n      pagination: { limit: $limit }\n    ) {\n      ...RouteBasic\n    }\n  }\n": typeof types.SearchRoutesDocument,
};
const documents: Documents = {
    "\n  \n  \n  mutation CreateRoute($data: RouteInput!) {\n    createRoute(data: $data) {\n      ...RouteBasic\n    }\n  }\n": types.CreateRouteDocument,
    "\n  \n  \n  mutation UpdateRoute($documentId: ID!, $data: RouteInput!) {\n    updateRoute(documentId: $documentId, data: $data) {\n      ...RouteBasic\n    }\n  }\n": types.UpdateRouteDocument,
    "\n  mutation DeleteRoute($documentId: ID!) {\n    deleteRoute(documentId: $documentId) {\n      documentId\n    }\n  }\n": types.DeleteRouteDocument,
    "\n  fragment RouteBasic on Route {\n    documentId\n    short_name\n    long_name\n    description\n    color\n    route_type\n  }\n": types.RouteBasicFragmentDoc,
    "\n  \n  \n  query GetRoutes($limit: Int, $start: Int, $sort: [String]) {\n    routes(\n      pagination: { limit: $limit, start: $start }\n      sort: $sort\n    ) {\n      ...RouteBasic\n    }\n  }\n": types.GetRoutesDocument,
    "\n  \n  \n  query GetRoute($documentId: ID!) {\n    route(documentId: $documentId) {\n      ...RouteBasic\n      createdAt\n      updatedAt\n    }\n  }\n": types.GetRouteDocument,
    "\n  \n  \n  query GetRouteByCode($shortName: String!) {\n    routes(filters: { short_name: { eq: $shortName } }) {\n      ...RouteBasic\n    }\n  }\n": types.GetRouteByCodeDocument,
    "\n  \n  \n  query SearchRoutes($search: String!, $limit: Int = 10) {\n    routes(\n      filters: {\n        or: [\n          { short_name: { containsi: $search } }\n          { long_name: { containsi: $search } }\n        ]\n      }\n      pagination: { limit: $limit }\n    ) {\n      ...RouteBasic\n    }\n  }\n": types.SearchRoutesDocument,
};

/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 *
 *
 * @example
 * ```ts
 * const query = gql(`query GetUser($id: ID!) { user(id: $id) { name } }`);
 * ```
 *
 * The query argument is unknown!
 * Please regenerate the types.
 */
export function gql(source: string): unknown;

/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  \n  \n  mutation CreateRoute($data: RouteInput!) {\n    createRoute(data: $data) {\n      ...RouteBasic\n    }\n  }\n"): (typeof documents)["\n  \n  \n  mutation CreateRoute($data: RouteInput!) {\n    createRoute(data: $data) {\n      ...RouteBasic\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  \n  \n  mutation UpdateRoute($documentId: ID!, $data: RouteInput!) {\n    updateRoute(documentId: $documentId, data: $data) {\n      ...RouteBasic\n    }\n  }\n"): (typeof documents)["\n  \n  \n  mutation UpdateRoute($documentId: ID!, $data: RouteInput!) {\n    updateRoute(documentId: $documentId, data: $data) {\n      ...RouteBasic\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  mutation DeleteRoute($documentId: ID!) {\n    deleteRoute(documentId: $documentId) {\n      documentId\n    }\n  }\n"): (typeof documents)["\n  mutation DeleteRoute($documentId: ID!) {\n    deleteRoute(documentId: $documentId) {\n      documentId\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  fragment RouteBasic on Route {\n    documentId\n    short_name\n    long_name\n    description\n    color\n    route_type\n  }\n"): (typeof documents)["\n  fragment RouteBasic on Route {\n    documentId\n    short_name\n    long_name\n    description\n    color\n    route_type\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  \n  \n  query GetRoutes($limit: Int, $start: Int, $sort: [String]) {\n    routes(\n      pagination: { limit: $limit, start: $start }\n      sort: $sort\n    ) {\n      ...RouteBasic\n    }\n  }\n"): (typeof documents)["\n  \n  \n  query GetRoutes($limit: Int, $start: Int, $sort: [String]) {\n    routes(\n      pagination: { limit: $limit, start: $start }\n      sort: $sort\n    ) {\n      ...RouteBasic\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  \n  \n  query GetRoute($documentId: ID!) {\n    route(documentId: $documentId) {\n      ...RouteBasic\n      createdAt\n      updatedAt\n    }\n  }\n"): (typeof documents)["\n  \n  \n  query GetRoute($documentId: ID!) {\n    route(documentId: $documentId) {\n      ...RouteBasic\n      createdAt\n      updatedAt\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  \n  \n  query GetRouteByCode($shortName: String!) {\n    routes(filters: { short_name: { eq: $shortName } }) {\n      ...RouteBasic\n    }\n  }\n"): (typeof documents)["\n  \n  \n  query GetRouteByCode($shortName: String!) {\n    routes(filters: { short_name: { eq: $shortName } }) {\n      ...RouteBasic\n    }\n  }\n"];
/**
 * The gql function is used to parse GraphQL queries into a document that can be used by GraphQL clients.
 */
export function gql(source: "\n  \n  \n  query SearchRoutes($search: String!, $limit: Int = 10) {\n    routes(\n      filters: {\n        or: [\n          { short_name: { containsi: $search } }\n          { long_name: { containsi: $search } }\n        ]\n      }\n      pagination: { limit: $limit }\n    ) {\n      ...RouteBasic\n    }\n  }\n"): (typeof documents)["\n  \n  \n  query SearchRoutes($search: String!, $limit: Int = 10) {\n    routes(\n      filters: {\n        or: [\n          { short_name: { containsi: $search } }\n          { long_name: { containsi: $search } }\n        ]\n      }\n      pagination: { limit: $limit }\n    ) {\n      ...RouteBasic\n    }\n  }\n"];

export function gql(source: string) {
  return (documents as any)[source] ?? {};
}

export type DocumentType<TDocumentNode extends DocumentNode<any, any>> = TDocumentNode extends DocumentNode<  infer TType,  any>  ? TType  : never;