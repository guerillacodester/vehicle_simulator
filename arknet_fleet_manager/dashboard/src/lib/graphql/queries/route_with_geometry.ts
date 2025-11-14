import { gql } from 'urql'

export const GET_ROUTE_WITH_GEOMETRY_QUERY = gql`
  query GetRouteWithGeometry($documentId: ID!) {
    route(documentId: $documentId) {
      documentId
      short_name
      long_name
      geojson_data
      createdAt
      updatedAt
    }
  }
`

export interface GetRouteWithGeometryVars {
  documentId: string
}

export interface RouteWithGeometryResult {
  route: {
    documentId: string
    short_name: string
    long_name?: string
    geojson_data?: any
    createdAt?: string
    updatedAt?: string
  }
}
