import { factories } from '@strapi/strapi';
import Redis from 'ioredis';
import * as zlib from 'zlib';
import { promisify } from 'util';

// Promisify zlib functions for async/await
const gzipAsync = promisify(zlib.gzip);
const ungzipAsync = promisify(zlib.gunzip);

// Initialize Redis client (default: localhost:6379)
// Make connection resilient and avoid unhandled error events when Redis
// is not started. Use a rate-limited error logger to avoid spamming logs.
const redisHost = process.env.REDIS_HOST ?? '127.0.0.1';
const redisPort = Number(process.env.REDIS_PORT ?? 6379);

const redis = new Redis({
  host: redisHost,
  port: redisPort,
  // Don't fail commands during reconnect windows
  maxRetriesPerRequest: null,
  // Control retry delays (ms)
  retryStrategy(times: number) {
    // linear backoff with cap
    const delay = Math.min(1000 + times * 200, 30000);
    return delay;
  },
  // Optionally attempt reconnect on certain errors
  reconnectOnError(err: Error) {
    const msg = String(err?.message ?? '');
    // only reconnect for transient network errors, not for auth/parse errors
    if (msg.includes('ECONNREFUSED') || msg.includes('ETIMEDOUT') || msg.includes('EHOSTUNREACH')) {
      return true;
    }
    return false;
  }
});

// Rate-limited redis error logging to prevent log spam when Redis is down
let _lastRedisErrorLog = 0;
const REDIS_ERROR_COOLDOWN_MS = Number(process.env.REDIS_ERROR_COOLDOWN_MS ?? 60000);
redis.on('error', (err) => {
  const now = Date.now();
  if (now - _lastRedisErrorLog > REDIS_ERROR_COOLDOWN_MS) {
    _lastRedisErrorLog = now;
    // Log minimal info to avoid complex objects causing further issues
    console.warn('[ioredis] connection error:', err && err.message ? err.message : String(err));
  }
});
redis.on('connect', () => console.debug('[ioredis] connecting...'));
redis.on('ready', () => console.info('[ioredis] ready'));
redis.on('end', () => console.warn('[ioredis] connection closed'));

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
  /**
   * Test Redis connectivity by setting and getting a value.
   * Returns true if successful, false otherwise.
   */
  async testRedisConnection() {
    try {
      await redis.set('strapi:redis:test', 'connected');
      const value = await redis.get('strapi:redis:test');
      return value === 'connected';
    } catch (err) {
      return false;
    }
  },
  async fetchRouteGeometry(routeShortName: string) {
    // Optimized cache key with versioning
    const cacheKey = `route:geometry:v2:${routeShortName}`;
    const metadataKey = `route:geometry:meta:v2:${routeShortName}`;

    try {
      // Check cache with metadata first
      const [cachedData, metadata] = await Promise.all([
        redis.getBuffer(cacheKey),
        redis.get(metadataKey)
      ]);

      if (cachedData && metadata) {
        const meta = JSON.parse(metadata);
        const decompressed = await ungzipAsync(cachedData);
        const result = JSON.parse(decompressed.toString());

        console.log(`[Redis Cache] HIT for route geometry: ${routeShortName} (${meta.size} bytes compressed, ${meta.accessCount} accesses)`);

        // Update access count and TTL (sliding expiration)
        const newAccessCount = meta.accessCount + 1;
        const newTTL = Math.min(3600 * 24, 3600 + (newAccessCount * 300)); // Max 24h, base 1h + 5min per access
        await redis.set(metadataKey, JSON.stringify({ ...meta, accessCount: newAccessCount }), 'EX', newTTL);
        await redis.expire(cacheKey, newTTL);

        return result;
      }

      console.log(`[Redis Cache] MISS for route geometry: ${routeShortName}`);
    } catch (err) {
      console.error(`[Redis Cache] Error reading cache for ${routeShortName}:`, err);
    }

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

    const result = { coords: finalCoords, segments: bestOrdering, metrics, raw: { routeShapes, shapePoints } };

    // Optimized cache storage with compression
    try {
      const jsonData = JSON.stringify(result);
      const compressed = await gzipAsync(Buffer.from(jsonData));

      // Calculate TTL based on data size and complexity
      const dataSize = compressed.length;
      const baseTTL = 3600; // 1 hour base
      const sizeBonus = Math.floor(dataSize / 10000) * 1800; // +30min per 10KB
      const complexityBonus = Math.floor(metrics.totalPoints / 1000) * 900; // +15min per 1000 points
      const ttl = Math.min(baseTTL + sizeBonus + complexityBonus, 86400); // Max 24 hours

      const metadata = {
        size: dataSize,
        uncompressedSize: jsonData.length,
        compressionRatio: (jsonData.length / dataSize).toFixed(2),
        totalPoints: metrics.totalPoints,
        segments: metrics.segments,
        accessCount: 1,
        created: new Date().toISOString(),
        ttl: ttl
      };

      // Store compressed data and metadata with same TTL
      await Promise.all([
        redis.setex(cacheKey, ttl, compressed),
        redis.setex(metadataKey, ttl, JSON.stringify(metadata))
      ]);

      console.log(`[Redis Cache] STORED route geometry: ${routeShortName} (${dataSize} bytes compressed, ratio: ${metadata.compressionRatio}x, TTL: ${Math.floor(ttl/3600)}h)`);
    } catch (err) {
      console.error(`[Redis Cache] Error storing cache for ${routeShortName}:`, err);
    }

    return result;
  },

  // Cache management utilities
  async invalidateRouteCache(routeShortName: string) {
    const cacheKey = `route:geometry:v2:${routeShortName}`;
    const metadataKey = `route:geometry:meta:v2:${routeShortName}`;

    try {
      const deleted = await redis.del([cacheKey, metadataKey]);
      console.log(`[Redis Cache] INVALIDATED route geometry: ${routeShortName} (${deleted} keys removed)`);
      return deleted > 0;
    } catch (err) {
      console.error(`[Redis Cache] Error invalidating cache for ${routeShortName}:`, err);
      return false;
    }
  },

  async getCacheStats(routeShortName?: string) {
    try {
      const pattern = routeShortName
        ? `route:geometry:meta:v2:${routeShortName}`
        : 'route:geometry:meta:v2:*';

      const keys = await redis.keys(pattern);
      const stats: {
        totalRoutes: number;
        totalSize: number;
        totalAccesses: number;
        routes: Array<{
          routeName: string;
          size: number;
          uncompressedSize: number;
          compressionRatio: string;
          totalPoints: number;
          segments: number;
          accessCount: number;
          created: string;
          ttl: number;
        }>;
      } = {
        totalRoutes: 0,
        totalSize: 0,
        totalAccesses: 0,
        routes: []
      };

      for (const key of keys) {
        const metadata = await redis.get(key);
        if (metadata) {
          const meta = JSON.parse(metadata);
          stats.totalRoutes++;
          stats.totalSize += meta.size;
          stats.totalAccesses += meta.accessCount;
          stats.routes.push({
            routeName: key.replace('route:geometry:meta:v2:', ''),
            ...meta
          });
        }
      }

      return stats;
    } catch (err) {
      console.error('[Redis Cache] Error getting cache stats:', err);
      return null;
    }
  },
}));
