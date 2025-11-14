import { gql } from 'urql';

/**
 * Query: get routeShapes for a route (returns shape_id list and ordering info)
 */
export const GET_ROUTE_SHAPES = gql`
  query GetRouteShapes($documentId: ID!, $routeShortName: String!, $limit: Int = 200) {
    route(documentId: $documentId) {
      documentId
      short_name
      long_name
    }

    routeShapes(filters: { route_id: { eq: $routeShortName } }, pagination: { limit: $limit }, sort: ["route_shape_id:asc"]) {
      route_shape_id
      shape_id
      is_default
      variant_code
    }
  }
`;

/**
 * Query: fetch all shape points for a list of shape_ids (returns Strapi collection format)
 */
export const GET_SHAPES_BY_IDS = gql`
  query GetShapesForRoute($shapeIds: [String], $limit: Int = 5000) {
    shapes(filters: { shape_id: { in: $shapeIds } }, pagination: { limit: $limit }, sort: ["shape_id:asc", "shape_pt_sequence:asc"]) {
      data {
        id
        attributes {
          shape_id
          shape_pt_sequence
          shape_pt_lat
          shape_pt_lon
          shape_dist_traveled
        }
      }
    }
  }
`;

/**
 * Convenience helper that runs the two queries using a urql Client and
 * assembles a single ordered coordinate array for the route.
 *
 * Usage (example):
 *   const res = await fetchRouteGeometry(client, documentId, "1");
 *   // res.coordinates -> Array<[lon, lat]>
 *
 * Notes:
 * - `client` must be an instance of urql Client (import { Client } from 'urql')
 * - The function groups points by shape_id and concatenates them in the order
 *   returned by `routeShapes` (so preserve that order for correct geometry).
 */
export async function fetchRouteGeometry(client: any, documentId: string, routeShortName: string) {
  const shapesResult = await client.query(GET_ROUTE_SHAPES, { documentId, routeShortName }).toPromise();
  const routeShapes = shapesResult?.data?.routeShapes || [];

  const shapeIds = Array.from(new Set(routeShapes.map((rs: any) => rs.shape_id).filter(Boolean)));

  if (shapeIds.length === 0) {
    return { coordinates: [], shapeIds: [], segments: 0 };
  }

  const ptsResult = await client.query(GET_SHAPES_BY_IDS, { shapeIds }).toPromise();
  const ptsData = ptsResult?.data?.shapes?.data || [];

  // Group points by shape_id preserving sequence
  const pointsByShape: Record<string, Array<[number, number]>> = {};
  for (const row of ptsData) {
    const attrs = row.attributes;
    if (!attrs) continue;
    const sid = attrs.shape_id;
    if (!pointsByShape[sid]) pointsByShape[sid] = [];
    pointsByShape[sid].push([attrs.shape_pt_lon, attrs.shape_pt_lat]);
  }

  // Assemble coordinates in routeShapes order
  const coordinates: Array<[number, number]> = [];
  for (const rs of routeShapes) {
    const sid = rs.shape_id;
    const seg = pointsByShape[sid] || [];
    // Append segment (do NOT dedupe endpoints here; caller can decide)
    coordinates.push(...seg);
  }

  return {
    coordinates,
    shapeIds,
    segments: routeShapes.length,
  };
}

export default GET_ROUTE_SHAPES;
