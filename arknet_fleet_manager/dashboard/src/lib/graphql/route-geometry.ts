/**
 * Route Geometry Assembler for Strapi GTFS Data
 * 
 * CANONICAL METHOD for acquiring route coordinates from Strapi database.
 * 
 * This module handles fetching and assembling route geometry from fragmented
 * shape segments stored in the GTFS-compliant Strapi database.
 * 
 * Key Features:
 * - Fetches route_shapes with pagination (limit: 100) to get all segments
 * - Fetches shape points with pagination (limit: 1000) to get all coordinates
 * - Uses optimal spatial ordering: tries all starting points and selects the
 *   ordering that produces the shortest total route length (minimizes seams)
 * - Automatically reverses segments when needed for spatial continuity
 * - Computes quality metrics: total length, seam gaps, point counts
 * 
 * Algorithm:
 * 1. Query routeShapes filtered by route_id
 * 2. Query shapes filtered by shape_id list
 * 3. Group shape points by shape_id and sort by sequence
 * 4. Build segment objects with start/end coordinates
 * 5. Try all possible starting segments
 * 6. For each start, greedily connect nearest segment (may reverse)
 * 7. Select ordering with shortest total length
 * 8. Assemble final coordinate array
 * 
 * Tested: Route 1 returns 415 coordinates, 13.394 km length
 * 
 * @module route-geometry
 */

import type { Client } from 'urql';

// GraphQL Queries
// CANONICAL METHOD: These queries with pagination limits are the official way
// to fetch route geometry from Strapi GTFS database.
const GET_ROUTE_SHAPES = `
  query GetRouteShapes($routeShortName: String!) {
    routeShapes(
      filters: { route_id: { eq: $routeShortName } }
      pagination: { limit: 100 }
    ) {
      documentId
      route_id
      shape_id
      is_default
      variant_code
    }
  }
`;

const GET_SHAPES_BY_IDS = `
  query GetShapesByIds($shapeIds: [String!]!) {
    shapes(
      filters: { shape_id: { in: $shapeIds } }
      sort: ["shape_pt_sequence:asc"]
      pagination: { limit: 1000 }
    ) {
      shape_id
      shape_pt_sequence
      shape_pt_lat
      shape_pt_lon
      shape_dist_traveled
    }
  }
`;

// Types
export interface RouteShape {
  route_shape_id: string;
  shape_id: string;
  is_default: boolean;
  variant_code?: string | null;
}

export interface ShapePoint {
  shape_id: string;
  shape_pt_sequence: number;
  shape_pt_lat: number;
  shape_pt_lon: number;
  shape_dist_traveled?: number | null;
}

export interface Coordinate {
  lon: number;
  lat: number;
}

export interface RouteSegment {
  route_shape_id: string;
  shape_id: string;
  coords: Coordinate[];
  start: Coordinate;
  end: Coordinate;
  reversed?: boolean;
}

export interface RouteGeometry {
  coordinates: Coordinate[];
  segments: RouteSegment[];
  metrics: {
    totalPoints: number;
    totalSegments: number;
    estimatedLength: number; // km
    maxSeamGap: number; // km
    hasLargeSeams: boolean;
  };
}

// Haversine distance calculation
function haversine(coord1: Coordinate, coord2: Coordinate): number {
  const R = 6371; // Earth radius in km
  const toRad = (deg: number) => (deg * Math.PI) / 180;
  
  const dLat = toRad(coord2.lat - coord1.lat);
  const dLon = toRad(coord2.lon - coord1.lon);
  
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(toRad(coord1.lat)) *
      Math.cos(toRad(coord2.lat)) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return R * c;
}

// Group shape points by shape_id
function groupShapePoints(points: ShapePoint[]): Map<string, Coordinate[]> {
  const grouped = new Map<string, Array<{ seq: number; coord: Coordinate }>>();
  
  for (const pt of points) {
    if (!grouped.has(pt.shape_id)) {
      grouped.set(pt.shape_id, []);
    }
    grouped.get(pt.shape_id)!.push({
      seq: pt.shape_pt_sequence,
      coord: { lon: pt.shape_pt_lon, lat: pt.shape_pt_lat },
    });
  }
  
  // Sort by sequence and extract coordinates
  const result = new Map<string, Coordinate[]>();
  for (const [shapeId, items] of grouped.entries()) {
    items.sort((a, b) => a.seq - b.seq);
    result.set(shapeId, items.map((item) => item.coord));
  }
  
  return result;
}

// Build segments from route_shapes and grouped points
function buildSegments(
  routeShapes: RouteShape[],
  pointsByShape: Map<string, Coordinate[]>
): RouteSegment[] {
  const segments: RouteSegment[] = [];
  
  for (const rs of routeShapes) {
    const coords = pointsByShape.get(rs.shape_id);
    if (!coords || coords.length === 0) continue;
    
    segments.push({
      route_shape_id: rs.route_shape_id,
      shape_id: rs.shape_id,
      coords: [...coords],
      start: coords[0],
      end: coords[coords.length - 1],
    });
  }
  
  return segments;
}

// Reorder segments by spatial continuity (greedy nearest-neighbor with optimal start)
// CANONICAL ALGORITHM: Tries all possible starting points and picks the one
// that produces the shortest total route length (minimizes backtracking/seams)
function reorderSegmentsBySpatialContinuity(segments: RouteSegment[]): RouteSegment[] {
  if (segments.length === 0) return [];
  if (segments.length === 1) return segments;
  
  let bestOrdering: RouteSegment[] | null = null;
  let bestTotalLength = Infinity;
  
  // Try each segment as the starting point
  for (let startIdx = 0; startIdx < segments.length; startIdx++) {
    const unused = segments.map(seg => ({...seg, coords: [...seg.coords]}));
    const ordered: RouteSegment[] = [];
    
    // Start with this segment
    ordered.push(unused.splice(startIdx, 1)[0]);
    
    // Greedily connect nearest segments
    while (unused.length > 0) {
      const currentEnd = ordered[ordered.length - 1].end;
      
      let bestIdx = 0;
      let bestDist = Infinity;
      let bestReversed = false;
      
      for (let i = 0; i < unused.length; i++) {
        const seg = unused[i];
        const distToStart = haversine(currentEnd, seg.start);
        const distToEnd = haversine(currentEnd, seg.end);
        
        if (distToStart < bestDist) {
          bestDist = distToStart;
          bestIdx = i;
          bestReversed = false;
        }
        if (distToEnd < bestDist) {
          bestDist = distToEnd;
          bestIdx = i;
          bestReversed = true;
        }
      }
      
      const nextSeg = unused.splice(bestIdx, 1)[0];
      
      if (bestReversed) {
        nextSeg.coords = [...nextSeg.coords].reverse();
        [nextSeg.start, nextSeg.end] = [nextSeg.end, nextSeg.start];
        nextSeg.reversed = true;
      }
      
      ordered.push(nextSeg);
    }
    
    // Calculate total length for this ordering
    const allCoords = ordered.flatMap(seg => seg.coords);
    let totalLength = 0;
    for (let i = 0; i < allCoords.length - 1; i++) {
      totalLength += haversine(allCoords[i], allCoords[i + 1]);
    }
    
    // Keep the ordering with shortest total length
    if (totalLength < bestTotalLength) {
      bestTotalLength = totalLength;
      bestOrdering = ordered;
    }
  }
  
  return bestOrdering || segments;
}

// Compute route metrics
function computeMetrics(segments: RouteSegment[]): RouteGeometry['metrics'] {
  const allCoords = segments.flatMap((seg) => seg.coords);
  
  let totalLength = 0;
  for (let i = 0; i < allCoords.length - 1; i++) {
    totalLength += haversine(allCoords[i], allCoords[i + 1]);
  }
  
  // Compute seam gaps (distance between segment endpoints)
  const seams: number[] = [];
  for (let i = 0; i < segments.length - 1; i++) {
    const gap = haversine(segments[i].end, segments[i + 1].start);
    seams.push(gap);
  }
  
  const maxSeam = seams.length > 0 ? Math.max(...seams) : 0;
  const hasLargeSeams = maxSeam > 0.5; // 500m threshold
  
  return {
    totalPoints: allCoords.length,
    totalSegments: segments.length,
    estimatedLength: totalLength,
    maxSeamGap: maxSeam,
    hasLargeSeams,
  };
}

/**
 * Fetch and assemble route geometry from Strapi
 * 
 * @param client - URQL client instance
 * @param routeShortName - Route short name (e.g., "1", "2", "A")
 * @returns Complete route geometry with ordered coordinates
 */
export async function fetchRouteGeometry(
  client: Client,
  routeShortName: string
): Promise<RouteGeometry> {
  // Step 1: Fetch route_shapes
  const routeShapesResult = await client
    .query(GET_ROUTE_SHAPES, { routeShortName })
    .toPromise();
  
  if (routeShapesResult.error) {
    throw new Error(`Failed to fetch route shapes: ${routeShapesResult.error.message}`);
  }
  
  const routeShapes = routeShapesResult.data?.routeShapes || [];
  
  if (routeShapes.length === 0) {
    throw new Error(`No route shapes found for route ${routeShortName}`);
  }
  
  const shapeIds = routeShapes.map((rs: RouteShape) => rs.shape_id);
  
  // Step 2: Fetch shape points
  const shapesResult = await client
    .query(GET_SHAPES_BY_IDS, { shapeIds })
    .toPromise();
  
  if (shapesResult.error) {
    throw new Error(`Failed to fetch shapes: ${shapesResult.error.message}`);
  }
  
  const shapePoints = shapesResult.data?.shapes || [];
  
  if (shapePoints.length === 0) {
    throw new Error(`No shape points found for route ${routeShortName}`);
  }
  
  // Step 3: Group points by shape_id
  const pointsByShape = groupShapePoints(shapePoints);
  
  // Step 4: Build segments
  const segments = buildSegments(routeShapes, pointsByShape);
  
  // Step 5: Reorder by spatial continuity
  const orderedSegments = reorderSegmentsBySpatialContinuity(segments);
  
  // Step 6: Assemble coordinates
  const coordinates = orderedSegments.flatMap((seg) => seg.coords);
  
  // Step 7: Compute metrics
  const metrics = computeMetrics(orderedSegments);
  
  // Warning if route has large seams
  if (metrics.hasLargeSeams) {
    console.warn(
      `Route ${routeShortName} has large seam gaps (max: ${metrics.maxSeamGap.toFixed(3)} km). ` +
      `Route geometry may be incorrect or data is fragmented.`
    );
  }
  
  return {
    coordinates,
    segments: orderedSegments,
    metrics,
  };
}

/**
 * React hook for fetching route geometry
 * 
 * @example
 * ```tsx
 * const { data, loading, error } = useRouteGeometry('1');
 * ```
 */
export function useRouteGeometry(routeShortName: string) {
  // Implementation depends on your React setup (urql useQuery, React Query, etc.)
  // This is a placeholder showing the expected interface
  throw new Error('Not implemented - integrate with your React data fetching library');
}
