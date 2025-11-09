import { factories } from '@strapi/strapi';

function haversine(a: [number, number], b: [number, number]): number {
  const R = 6371.0;
  const toRad = (v: number) => (v * Math.PI) / 180.0;
  const [lon1, lat1] = a;
  const [lon2, lat2] = b;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const lat1r = toRad(lat1);
  const lat2r = toRad(lat2);
  const s = Math.sin(dLat / 2) ** 2 + Math.cos(lat1r) * Math.cos(lat2r) * Math.sin(dLon / 2) ** 2;
  const c = 2 * Math.atan2(Math.sqrt(s), Math.sqrt(1 - s));
  return R * c;
}

export default factories.createCoreService('api::route.route', ({ strapi }) => ({
  async fetchRouteGeometry(routeShortName: string) {
    const routeShapes = await strapi.entityService.findMany('api::route-shape.route-shape', {
      filters: { route_id: { $eq: routeShortName } },
      limit: 200,
    });

    if (!routeShapes || routeShapes.length === 0) {
      return { coords: [], segments: [], metrics: null, raw: { routeShapes: [], shapePoints: [] } };
    }

    const shapeIds = routeShapes.map((rs: any) => rs.shape_id);

    const shapePoints = await strapi.entityService.findMany('api::shape.shape', {
      filters: { shape_id: { $in: shapeIds } },
      sort: { shape_pt_sequence: 'asc' },
      limit: 20000,
    });

    const pointsByShape: Record<string, Array<[number, number, number]>> = {};
    for (const pt of shapePoints) {
      const sid = pt.shape_id as string;
      pointsByShape[sid] = pointsByShape[sid] || [];
      pointsByShape[sid].push([pt.shape_pt_sequence as number, pt.shape_pt_lon as number, pt.shape_pt_lat as number]);
    }

    for (const sid of Object.keys(pointsByShape)) {
      pointsByShape[sid].sort((a, b) => a[0] - b[0]);
    }

    const segments: Array<any> = [];
    for (const rs of routeShapes) {
      const sid = rs.shape_id as string;
      const pts = pointsByShape[sid] || [];
      if (!pts.length) continue;
      const coords = pts.map(([_seq, lon, lat]) => [lon, lat]);
      segments.push({ shape_id: sid, coords, start: coords[0], end: coords[coords.length - 1] });
    }

    if (segments.length === 0) {
      return { coords: [], segments: [], metrics: null, raw: { routeShapes, shapePoints } };
    }

    let bestOrdering: Array<any> | null = null;
    let bestLength = Number.POSITIVE_INFINITY;

    for (let startIdx = 0; startIdx < segments.length; startIdx++) {
      const unused = segments.map((s) => ({ ...s }));
      const ordered: Array<any> = [];
      ordered.push(unused.splice(startIdx, 1)[0]);

      while (unused.length) {
        const currentEnd = ordered[ordered.length - 1].end;
        let bestIdx = 0;
        let bestDist = Number.POSITIVE_INFINITY;
        let shouldReverse = false;

        for (let i = 0; i < unused.length; i++) {
          const seg = unused[i];
          const distStart = haversine(currentEnd, seg.start);
          const distEnd = haversine(currentEnd, seg.end);
          if (distStart < bestDist) {
            bestDist = distStart;
            bestIdx = i;
            shouldReverse = false;
          }
          if (distEnd < bestDist) {
            bestDist = distEnd;
            bestIdx = i;
            shouldReverse = true;
          }
        }

        const next = { ...unused.splice(bestIdx, 1)[0] };
        if (shouldReverse) {
          next.coords = [...next.coords].reverse();
          next.start = next.coords[0];
          next.end = next.coords[next.coords.length - 1];
          next.reversed = true;
        }
        ordered.push(next);
      }

      const allCoords: Array<[number, number]> = [];
      for (const seg of ordered) allCoords.push(...seg.coords);
      let total = 0;
      for (let i = 0; i < allCoords.length - 1; i++) total += haversine(allCoords[i], allCoords[i + 1]);

      if (total < bestLength) {
        bestLength = total;
        bestOrdering = ordered;
      }
    }

    const finalCoords: Array<[number, number]> = [];
    for (const seg of bestOrdering!) finalCoords.push(...seg.coords);

    const metrics = {
      totalPoints: finalCoords.length,
      estimatedLengthKm: bestLength,
      segments: bestOrdering!.length,
      reversedCount: bestOrdering!.filter((s: any) => s.reversed).length,
    };

    return { coords: finalCoords, segments: bestOrdering, metrics, raw: { routeShapes, shapePoints } };
  },
}));
