"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
var _a, _b, _c;
Object.defineProperty(exports, "__esModule", { value: true });
const strapi_1 = require("@strapi/strapi");
const ioredis_1 = __importDefault(require("ioredis"));
// Initialize Redis client (default: localhost:6379)
// Make connection resilient and avoid unhandled error events when Redis
// is not started. Use a rate-limited error logger to avoid spamming logs.
const redisHost = (_a = process.env.REDIS_HOST) !== null && _a !== void 0 ? _a : '127.0.0.1';
const redisPort = Number((_b = process.env.REDIS_PORT) !== null && _b !== void 0 ? _b : 6379);
const redis = new ioredis_1.default({
    host: redisHost,
    port: redisPort,
    // Don't fail commands during reconnect windows
    maxRetriesPerRequest: null,
    // Control retry delays (ms)
    retryStrategy(times) {
        // linear backoff with cap
        const delay = Math.min(1000 + times * 200, 30000);
        return delay;
    },
    // Optionally attempt reconnect on certain errors
    reconnectOnError(err) {
        var _a;
        const msg = String((_a = err === null || err === void 0 ? void 0 : err.message) !== null && _a !== void 0 ? _a : '');
        // only reconnect for transient network errors, not for auth/parse errors
        if (msg.includes('ECONNREFUSED') || msg.includes('ETIMEDOUT') || msg.includes('EHOSTUNREACH')) {
            return true;
        }
        return false;
    }
});
// Rate-limited redis error logging to prevent log spam when Redis is down
let _lastRedisErrorLog = 0;
const REDIS_ERROR_COOLDOWN_MS = Number((_c = process.env.REDIS_ERROR_COOLDOWN_MS) !== null && _c !== void 0 ? _c : 60000);
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
function haversine(a, b) {
    const R = 6371.0;
    const toRad = (v) => (v * Math.PI) / 180.0;
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
exports.default = strapi_1.factories.createCoreService('api::route.route', ({ strapi }) => ({
    /**
     * Test Redis connectivity by setting and getting a value.
     * Returns true if successful, false otherwise.
     */
    async testRedisConnection() {
        try {
            await redis.set('strapi:redis:test', 'connected');
            const value = await redis.get('strapi:redis:test');
            return value === 'connected';
        }
        catch (err) {
            return false;
        }
    },
    async fetchRouteGeometry(routeShortName) {
        // Check Redis cache first
        const cacheKey = `route:geometry:${routeShortName}`;
        try {
            const cached = await redis.get(cacheKey);
            if (cached) {
                console.log(`[Redis Cache] HIT for route geometry: ${routeShortName}`);
                return JSON.parse(cached);
            }
            console.log(`[Redis Cache] MISS for route geometry: ${routeShortName}`);
        }
        catch (err) {
            console.error(`[Redis Cache] Error reading cache for ${routeShortName}:`, err);
        }
        const routeShapes = await strapi.entityService.findMany('api::route-shape.route-shape', {
            filters: { route_id: { $eq: routeShortName } },
            limit: 200,
        });
        if (!routeShapes || routeShapes.length === 0) {
            return { coords: [], segments: [], metrics: null, raw: { routeShapes: [], shapePoints: [] } };
        }
        const shapeIds = routeShapes.map((rs) => rs.shape_id);
        const shapePoints = await strapi.entityService.findMany('api::shape.shape', {
            filters: { shape_id: { $in: shapeIds } },
            sort: { shape_pt_sequence: 'asc' },
            limit: 20000,
        });
        const pointsByShape = {};
        for (const pt of shapePoints) {
            const sid = pt.shape_id;
            pointsByShape[sid] = pointsByShape[sid] || [];
            pointsByShape[sid].push([pt.shape_pt_sequence, pt.shape_pt_lon, pt.shape_pt_lat]);
        }
        for (const sid of Object.keys(pointsByShape)) {
            pointsByShape[sid].sort((a, b) => a[0] - b[0]);
        }
        const segments = [];
        for (const rs of routeShapes) {
            const sid = rs.shape_id;
            const pts = pointsByShape[sid] || [];
            if (!pts.length)
                continue;
            const coords = pts.map(([_seq, lon, lat]) => [lon, lat]);
            segments.push({ shape_id: sid, coords, start: coords[0], end: coords[coords.length - 1] });
        }
        if (segments.length === 0) {
            return { coords: [], segments: [], metrics: null, raw: { routeShapes, shapePoints } };
        }
        let bestOrdering = null;
        let bestLength = Number.POSITIVE_INFINITY;
        for (let startIdx = 0; startIdx < segments.length; startIdx++) {
            const unused = segments.map((s) => ({ ...s }));
            const ordered = [];
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
            const allCoords = [];
            for (const seg of ordered)
                allCoords.push(...seg.coords);
            let total = 0;
            for (let i = 0; i < allCoords.length - 1; i++)
                total += haversine(allCoords[i], allCoords[i + 1]);
            if (total < bestLength) {
                bestLength = total;
                bestOrdering = ordered;
            }
        }
        const finalCoords = [];
        for (const seg of bestOrdering)
            finalCoords.push(...seg.coords);
        const metrics = {
            totalPoints: finalCoords.length,
            estimatedLengthKm: bestLength,
            segments: bestOrdering.length,
            reversedCount: bestOrdering.filter((s) => s.reversed).length,
        };
        const result = { coords: finalCoords, segments: bestOrdering, metrics, raw: { routeShapes, shapePoints } };
        // Cache the result in Redis (TTL: 1 hour = 3600 seconds)
        try {
            await redis.set(cacheKey, JSON.stringify(result), 'EX', 3600);
            console.log(`[Redis Cache] STORED route geometry: ${routeShortName} (TTL: 1 hour)`);
        }
        catch (err) {
            console.error(`[Redis Cache] Error storing cache for ${routeShortName}:`, err);
        }
        return result;
    },
}));
//# sourceMappingURL=route.js.map