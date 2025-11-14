"use strict";
/**
 * GeoJSON Import Controller
 * Handles GeoJSON file imports with streaming parser and Socket.IO progress updates
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
const geojson_stream_parser_1 = require("../../../utils/geojson-stream-parser");
// Helper function to generate a slug/UID
function generateSlug(name, suffix) {
    const slug = name
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
    return suffix ? `${slug}-${suffix}` : slug;
}
exports.default = {
    /**
     * Health check endpoint
     */
    async health(ctx) {
        ctx.body = {
            status: 'ok',
            message: 'GeoJSON Import API is running',
            endpoints: [
                'POST /api/import-geojson/highway',
                'POST /api/import-geojson/amenity',
                'POST /api/import-geojson/landuse',
                'POST /api/import-geojson/building',
                'POST /api/import-geojson/admin',
            ],
        };
    },
    /**
     * Import highway.geojson (road network)
     * File: sample_data/highway.geojson (22,719 features, 43MB)
     * Target: highway table
     */
    async importHighway(ctx) {
        try {
            const { countryId } = ctx.request.body;
            if (!countryId) {
                return ctx.badRequest('countryId is required');
            }
            // Get the numeric country ID from the document ID using direct SQL
            const knex = strapi.db.connection;
            const countryResult = await knex('countries')
                .select('id')
                .where('document_id', countryId)
                .first();
            if (!countryResult) {
                return ctx.notFound(`Country not found: ${countryId}`);
            }
            const numericCountryId = countryResult.id;
            const jobId = `highway_${Date.now()}`;
            const startTime = Date.now();
            const geojsonPath = path_1.default.join(process.cwd(), '..', '..', 'sample_data', 'highway.geojson');
            if (!fs_1.default.existsSync(geojsonPath)) {
                strapi.log.error(`[${jobId}] Highway GeoJSON file not found: ${geojsonPath}`);
                return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
            }
            const stats = fs_1.default.statSync(geojsonPath);
            const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
            strapi.log.info(`[${jobId}] Starting STREAMING import of ${fileSizeMB} MB file`);
            // @ts-ignore
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'highway',
                phase: 'starting',
                fileSizeMB,
            });
            let totalProcessed = 0;
            const result = await (0, geojson_stream_parser_1.streamGeoJSON)(geojsonPath, {
                batchSize: 500,
                onBatch: async (features) => {
                    const timestamp = new Date();
                    const { randomUUID } = require('crypto');
                    const insertValues = [];
                    const insertBindings = [];
                    features.forEach((feature) => {
                        const props = feature.properties || {};
                        // Skip if no LineString geometry
                        if (!feature.geometry || feature.geometry.type !== 'LineString') {
                            return;
                        }
                        const roadName = props.name || props.ref || `${props.highway || 'road'}-${props.osm_id || 'unknown'}`;
                        const highwayId = generateSlug(roadName, props.osm_id);
                        const documentId = randomUUID();
                        // Convert LineString to WKT
                        const coordinates = feature.geometry.coordinates;
                        const wktCoords = coordinates.map((coord) => `${coord[0]} ${coord[1]}`).join(', ');
                        const wkt = `LINESTRING(${wktCoords})`;
                        insertValues.push('(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?)');
                        insertBindings.push(documentId, highwayId, props.osm_id || null, props.full_id || null, props.highway || 'other', roadName, props.ref || null, props.surface || null, props.lanes ? parseInt(props.lanes) : null, props.maxspeed || null, props.oneway === 'yes' ? true : (props.oneway === 'no' ? false : null), wkt, timestamp, timestamp, timestamp);
                    });
                    if (insertValues.length > 0) {
                        await knex.raw(`
              INSERT INTO highways (
                document_id, highway_id, osm_id, full_id, highway_type, name,
                ref, surface, lanes, maxspeed, oneway, geom,
                created_at, updated_at, published_at
              ) VALUES ${insertValues.join(', ')}
            `, insertBindings);
                        const highwayIds = await knex('highways')
                            .select('id')
                            .whereIn('highway_id', features.filter((f) => {
                            return f.geometry && f.geometry.type === 'LineString';
                        }).map((f) => {
                            const props = f.properties || {};
                            const roadName = props.name || props.ref || `${props.highway || 'road'}-${props.osm_id || 'unknown'}`;
                            return generateSlug(roadName, props.osm_id);
                        }))
                            .orderBy('id', 'desc')
                            .limit(insertValues.length);
                        const countryLinkBindings = [];
                        const countryLinkPlaceholders = highwayIds.map((row) => {
                            countryLinkBindings.push(row.id, numericCountryId);
                            return '(?, ?)';
                        }).join(', ');
                        if (countryLinkPlaceholders) {
                            await knex.raw(`
                INSERT INTO highways_country_lnk (highway_id, country_id)
                VALUES ${countryLinkPlaceholders}
              `, countryLinkBindings);
                        }
                    }
                    totalProcessed += features.length;
                },
                onProgress: (progress) => {
                    const elapsedSeconds = (progress.elapsedTime / 1000).toFixed(1);
                    const featuresPerSecond = progress.elapsedTime > 0
                        ? (progress.processed / (progress.elapsedTime / 1000)).toFixed(0)
                        : '0';
                    // @ts-ignore
                    strapi.io.emit('import:progress', {
                        jobId,
                        countryId,
                        fileType: 'highway',
                        processed: progress.processed,
                        estimatedTotal: progress.estimatedTotal,
                        currentBatch: progress.currentBatch,
                        elapsedTime: progress.elapsedTime,
                        elapsedSeconds,
                        featuresPerSecond,
                    });
                    strapi.log.info(`[${jobId}] Progress: ${progress.processed} features | Batch ${progress.currentBatch} | ${elapsedSeconds}s elapsed | ${featuresPerSecond} features/sec`);
                },
                onError: (error) => {
                    strapi.log.error(`[${jobId}] Streaming error:`, error);
                    // @ts-ignore
                    strapi.io.emit('import:error', {
                        jobId,
                        countryId,
                        fileType: 'highway',
                        error: error.message,
                    });
                },
            });
            const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
            const featuresPerSecond = (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0);
            strapi.log.info(`[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s (${result.totalBatches} batches, ${featuresPerSecond} features/sec)`);
            // Link all highways to regions via spatial intersection (after import completes)
            const regionLinkStart = Date.now();
            strapi.log.info(`[${jobId}] Linking highways to regions...`);
            // @ts-ignore
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'highway',
                phase: 'linking-regions',
                message: 'Linking highways to regions...',
            });
            await knex.raw(`
        INSERT INTO highways_region_lnk (highway_id, region_id)
        SELECT h.id, r.id
        FROM highways h
        JOIN regions r ON ST_Intersects(h.geom, r.geom)
        WHERE h.id NOT IN (SELECT highway_id FROM highways_region_lnk)
      `);
            const regionLinkResult = await knex('highways_region_lnk').count('* as count').first();
            const regionLinkCount = (regionLinkResult === null || regionLinkResult === void 0 ? void 0 : regionLinkResult.count) || 0;
            const regionLinkElapsed = ((Date.now() - regionLinkStart) / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Region linking COMPLETE: ${regionLinkCount} links created in ${regionLinkElapsed}s`);
            // @ts-ignore
            strapi.io.emit('import:complete', {
                jobId,
                countryId,
                fileType: 'highway',
                totalFeatures: result.totalFeatures,
                elapsedSeconds,
                featuresPerSecond,
                regionLinks: regionLinkCount,
                regionLinkElapsed,
            });
            ctx.body = {
                jobId,
                message: 'Highway import completed successfully',
                countryId,
                fileType: 'highway',
                result: {
                    totalFeatures: result.totalFeatures,
                    totalBatches: result.totalBatches,
                    elapsedSeconds,
                    featuresPerSecond,
                    regionLinks: regionLinkCount,
                    regionLinkElapsed,
                },
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            strapi.log.error('Highway import failed:', error);
            ctx.internalServerError(`Import failed: ${errorMessage}`);
        }
    },
    /**
     * Import amenity.geojson (POIs for passenger spawning)
     * File: sample_data/amenity.geojson (1,427 features, 3.8MB)
     * Target: poi table
     * Note: Extracts centroids from Polygon/MultiPolygon geometries to store as POINT
     */
    async importAmenity(ctx) {
        try {
            const { countryId } = ctx.request.body;
            if (!countryId) {
                return ctx.badRequest('countryId is required');
            }
            // Get the numeric country ID from the document ID using direct SQL
            const knex = strapi.db.connection;
            const countryResult = await knex('countries')
                .select('id')
                .where('document_id', countryId)
                .first();
            if (!countryResult) {
                return ctx.notFound(`Country not found: ${countryId}`);
            }
            const numericCountryId = countryResult.id;
            const jobId = `amenity_${Date.now()}`;
            const startTime = Date.now();
            const geojsonPath = path_1.default.join(process.cwd(), '..', '..', 'sample_data', 'amenity.geojson');
            if (!fs_1.default.existsSync(geojsonPath)) {
                strapi.log.error(`[${jobId}] Amenity GeoJSON file not found: ${geojsonPath}`);
                return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
            }
            const stats = fs_1.default.statSync(geojsonPath);
            const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
            strapi.log.info(`[${jobId}] Starting STREAMING import of ${fileSizeMB} MB file`);
            // @ts-ignore
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'amenity',
                phase: 'starting',
                fileSizeMB,
            });
            let totalProcessed = 0;
            const result = await (0, geojson_stream_parser_1.streamGeoJSON)(geojsonPath, {
                batchSize: 500,
                onBatch: async (features) => {
                    const knex = strapi.db.connection;
                    const timestamp = new Date();
                    const { randomUUID } = require('crypto');
                    const insertValues = [];
                    const insertBindings = [];
                    for (const feature of features) {
                        const props = feature.properties || {};
                        // Skip if no geometry
                        if (!feature.geometry) {
                            continue;
                        }
                        const poiName = props.name || props.amenity || `${props.amenity || 'poi'}-${props.osm_id || 'unknown'}`;
                        const poiId = generateSlug(poiName, props.osm_id);
                        const documentId = randomUUID();
                        // Extract centroid coordinates based on geometry type
                        let longitude;
                        let latitude;
                        let wkt;
                        if (feature.geometry.type === 'Point') {
                            const coords = feature.geometry.coordinates;
                            longitude = coords[0];
                            latitude = coords[1];
                            wkt = `POINT(${longitude} ${latitude})`;
                        }
                        else if (feature.geometry.type === 'Polygon') {
                            // Use PostGIS ST_Centroid to extract center point
                            const coords = feature.geometry.coordinates[0]; // exterior ring
                            const wktCoords = coords.map((c) => `${c[0]} ${c[1]}`).join(', ');
                            const polygonWkt = `POLYGON((${wktCoords}))`;
                            // Calculate centroid in SQL and extract coordinates
                            const centroidResult = await knex.raw(`
                SELECT ST_X(ST_Centroid(ST_GeomFromText(?, 4326))) as lon,
                       ST_Y(ST_Centroid(ST_GeomFromText(?, 4326))) as lat
              `, [polygonWkt, polygonWkt]);
                            longitude = centroidResult.rows[0].lon;
                            latitude = centroidResult.rows[0].lat;
                            wkt = `POINT(${longitude} ${latitude})`;
                        }
                        else if (feature.geometry.type === 'MultiPolygon') {
                            // Use PostGIS ST_Centroid for MultiPolygon
                            const polygons = feature.geometry.coordinates.map((polygon) => {
                                const ring = polygon[0];
                                const wktCoords = ring.map((c) => `${c[0]} ${c[1]}`).join(', ');
                                return `((${wktCoords}))`;
                            }).join(', ');
                            const multiPolygonWkt = `MULTIPOLYGON(${polygons})`;
                            const centroidResult = await knex.raw(`
                SELECT ST_X(ST_Centroid(ST_GeomFromText(?, 4326))) as lon,
                       ST_Y(ST_Centroid(ST_GeomFromText(?, 4326))) as lat
              `, [multiPolygonWkt, multiPolygonWkt]);
                            longitude = centroidResult.rows[0].lon;
                            latitude = centroidResult.rows[0].lat;
                            wkt = `POINT(${longitude} ${latitude})`;
                        }
                        else {
                            // Skip unsupported geometry types
                            continue;
                        }
                        insertValues.push('(?, ?, ?, ?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?)');
                        insertBindings.push(documentId, props.osm_id || null, props.amenity || 'other', poiName, props.amenity || null, latitude, longitude, wkt, timestamp, timestamp, timestamp);
                    }
                    if (insertValues.length > 0) {
                        await knex.raw(`
              INSERT INTO pois (
                document_id, osm_id, poi_type, name,
                amenity, latitude, longitude, geom,
                created_at, updated_at, published_at
              ) VALUES ${insertValues.join(', ')}
            `, insertBindings);
                    }
                    totalProcessed += features.length;
                },
                onProgress: (progress) => {
                    const elapsedSeconds = (progress.elapsedTime / 1000).toFixed(1);
                    const featuresPerSecond = progress.elapsedTime > 0
                        ? (progress.processed / (progress.elapsedTime / 1000)).toFixed(0)
                        : '0';
                    // @ts-ignore
                    strapi.io.emit('import:progress', {
                        jobId,
                        countryId,
                        fileType: 'amenity',
                        processed: progress.processed,
                        estimatedTotal: progress.estimatedTotal,
                        currentBatch: progress.currentBatch,
                        elapsedTime: progress.elapsedTime,
                        elapsedSeconds,
                        featuresPerSecond,
                    });
                    strapi.log.info(`[${jobId}] Progress: ${progress.processed} features | Batch ${progress.currentBatch} | ${elapsedSeconds}s elapsed | ${featuresPerSecond} features/sec`);
                },
                onError: (error) => {
                    strapi.log.error(`[${jobId}] Streaming error:`, error);
                    // @ts-ignore
                    strapi.io.emit('import:error', {
                        jobId,
                        countryId,
                        fileType: 'amenity',
                        error: error.message,
                    });
                },
            });
            const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
            const featuresPerSecond = (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0);
            strapi.log.info(`[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s (${result.totalBatches} batches, ${featuresPerSecond} features/sec)`);
            // Phase 2: Link POIs to country
            strapi.log.info(`[${jobId}] 🔗 Starting country linking for POIs...`);
            const countryLinkStart = Date.now();
            const countryLinkResult = await knex.raw(`
        INSERT INTO pois_country_lnk (poi_id, country_id)
        SELECT p.id, ?
        FROM pois p
        WHERE p.id NOT IN (SELECT poi_id FROM pois_country_lnk)
      `, [numericCountryId]);
            const countryLinkCount = (countryLinkResult === null || countryLinkResult === void 0 ? void 0 : countryLinkResult.rowCount) || 0;
            const countryLinkElapsed = ((Date.now() - countryLinkStart) / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Country linking COMPLETE: ${countryLinkCount} links created in ${countryLinkElapsed}s`);
            // Phase 3: Link POIs to regions
            strapi.log.info(`[${jobId}] 🔗 Starting region linking for POIs...`);
            // @ts-ignore
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'amenity',
                message: 'Linking POIs to regions...',
            });
            const regionLinkStart = Date.now();
            const regionLinkResult = await knex.raw(`
        INSERT INTO pois_region_lnk (poi_id, region_id)
        SELECT p.id, r.id
        FROM pois p
        JOIN regions r ON ST_Intersects(p.geom, r.geom)
        WHERE p.id NOT IN (SELECT poi_id FROM pois_region_lnk)
      `);
            const regionLinkCount = (regionLinkResult === null || regionLinkResult === void 0 ? void 0 : regionLinkResult.rowCount) || 0;
            const regionLinkElapsed = ((Date.now() - regionLinkStart) / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Region linking COMPLETE: ${regionLinkCount} links created in ${regionLinkElapsed}s`);
            // @ts-ignore
            strapi.io.emit('import:complete', {
                jobId,
                countryId,
                fileType: 'amenity',
                totalFeatures: result.totalFeatures,
                elapsedSeconds,
                featuresPerSecond,
                countryLinkCount,
                regionLinkCount,
            });
            ctx.body = {
                jobId,
                message: 'Amenity import completed successfully',
                countryId,
                fileType: 'amenity',
                result: {
                    totalFeatures: result.totalFeatures,
                    totalBatches: result.totalBatches,
                    elapsedSeconds,
                    featuresPerSecond,
                    countryLinkCount,
                    regionLinkCount,
                },
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            strapi.log.error('Amenity import failed:', error);
            ctx.internalServerError(`Import failed: ${errorMessage}`);
        }
    },
    /**
     * Import landuse.geojson (zones with population density)
     * File: sample_data/landuse.geojson (2,267 features, 4.3MB)
     * Target: landuse_zone table
     */
    async importLanduse(ctx) {
        try {
            const { countryId } = ctx.request.body;
            if (!countryId) {
                return ctx.badRequest('countryId is required');
            }
            // Get the numeric country ID from the document ID using direct SQL
            const knex = strapi.db.connection;
            const countryResult = await knex('countries')
                .select('id')
                .where('document_id', countryId)
                .first();
            if (!countryResult) {
                return ctx.notFound(`Country not found: ${countryId}`);
            }
            const numericCountryId = countryResult.id;
            const jobId = `landuse_${Date.now()}`;
            const startTime = Date.now();
            const geojsonPath = path_1.default.join(process.cwd(), '..', '..', 'sample_data', 'landuse.geojson');
            if (!fs_1.default.existsSync(geojsonPath)) {
                strapi.log.error(`[${jobId}] Landuse GeoJSON file not found: ${geojsonPath}`);
                return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
            }
            const stats = fs_1.default.statSync(geojsonPath);
            const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
            strapi.log.info(`[${jobId}] Starting STREAMING import of ${fileSizeMB} MB file`);
            // @ts-ignore
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'landuse',
                phase: 'starting',
                fileSizeMB,
            });
            let totalProcessed = 0;
            const result = await (0, geojson_stream_parser_1.streamGeoJSON)(geojsonPath, {
                batchSize: 500,
                onBatch: async (features) => {
                    const knex = strapi.db.connection;
                    const timestamp = new Date();
                    const { randomUUID } = require('crypto');
                    const insertValues = [];
                    const insertBindings = [];
                    features.forEach((feature) => {
                        const props = feature.properties || {};
                        // Skip if no Polygon/MultiPolygon geometry
                        if (!feature.geometry || !['Polygon', 'MultiPolygon'].includes(feature.geometry.type)) {
                            return;
                        }
                        const zoneName = props.name || `${props.landuse || 'zone'}-${props.osm_id || 'unknown'}`;
                        const documentId = randomUUID();
                        // Convert Polygon/MultiPolygon to WKT
                        let wkt;
                        if (feature.geometry.type === 'Polygon') {
                            const rings = feature.geometry.coordinates.map((ring) => {
                                const coords = ring.map((c) => `${c[0]} ${c[1]}`).join(', ');
                                return `(${coords})`;
                            }).join(', ');
                            wkt = `POLYGON(${rings})`;
                        }
                        else {
                            // MultiPolygon
                            const polygons = feature.geometry.coordinates.map((polygon) => {
                                const rings = polygon.map((ring) => {
                                    const coords = ring.map((c) => `${c[0]} ${c[1]}`).join(', ');
                                    return `(${coords})`;
                                }).join(', ');
                                return `(${rings})`;
                            }).join(', ');
                            wkt = `MULTIPOLYGON(${polygons})`;
                        }
                        insertValues.push('(?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?)');
                        insertBindings.push(documentId, props.osm_id || null, props.landuse || 'other', zoneName, wkt, timestamp, timestamp, timestamp);
                    });
                    if (insertValues.length > 0) {
                        await knex.raw(`
              INSERT INTO landuse_zones (
                document_id, osm_id, zone_type, name,
                geom, created_at, updated_at, published_at
              ) VALUES ${insertValues.join(', ')}
            `, insertBindings);
                    }
                    totalProcessed += features.length;
                },
                onProgress: (progress) => {
                    const elapsedSeconds = (progress.elapsedTime / 1000).toFixed(1);
                    const featuresPerSecond = progress.elapsedTime > 0
                        ? (progress.processed / (progress.elapsedTime / 1000)).toFixed(0)
                        : '0';
                    // @ts-ignore
                    strapi.io.emit('import:progress', {
                        jobId,
                        countryId,
                        fileType: 'landuse',
                        processed: progress.processed,
                        estimatedTotal: progress.estimatedTotal,
                        currentBatch: progress.currentBatch,
                        elapsedTime: progress.elapsedTime,
                        elapsedSeconds,
                        featuresPerSecond,
                    });
                    strapi.log.info(`[${jobId}] Progress: ${progress.processed} features | Batch ${progress.currentBatch} | ${elapsedSeconds}s elapsed | ${featuresPerSecond} features/sec`);
                },
                onError: (error) => {
                    strapi.log.error(`[${jobId}] Streaming error:`, error);
                    // @ts-ignore
                    strapi.io.emit('import:error', {
                        jobId,
                        countryId,
                        fileType: 'landuse',
                        error: error.message,
                    });
                },
            });
            const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
            const featuresPerSecond = (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0);
            strapi.log.info(`[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s (${result.totalBatches} batches, ${featuresPerSecond} features/sec)`);
            // Phase 2: Link landuse zones to country
            strapi.log.info(`[${jobId}] 🔗 Starting country linking for landuse zones...`);
            const countryLinkStart = Date.now();
            const countryLinkResult = await knex.raw(`
        INSERT INTO landuse_zones_country_lnk (landuse_zone_id, country_id)
        SELECT lz.id, ?
        FROM landuse_zones lz
        WHERE lz.id NOT IN (SELECT landuse_zone_id FROM landuse_zones_country_lnk)
      `, [numericCountryId]);
            const countryLinkCount = (countryLinkResult === null || countryLinkResult === void 0 ? void 0 : countryLinkResult.rowCount) || 0;
            const countryLinkElapsed = ((Date.now() - countryLinkStart) / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Country linking COMPLETE: ${countryLinkCount} links created in ${countryLinkElapsed}s`);
            // Phase 3: Link landuse zones to regions
            strapi.log.info(`[${jobId}] 🔗 Starting region linking for landuse zones...`);
            const regionLinkStart = Date.now();
            const regionLinkResult = await knex.raw(`
        INSERT INTO landuse_zones_region_lnk (landuse_zone_id, region_id)
        SELECT lz.id, r.id
        FROM landuse_zones lz
        JOIN regions r ON ST_Intersects(lz.geom, r.geom)
        WHERE lz.id NOT IN (SELECT landuse_zone_id FROM landuse_zones_region_lnk)
      `);
            const regionLinkCount = (regionLinkResult === null || regionLinkResult === void 0 ? void 0 : regionLinkResult.rowCount) || 0;
            const regionLinkElapsed = ((Date.now() - regionLinkStart) / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Region linking COMPLETE: ${regionLinkCount} links created in ${regionLinkElapsed}s`);
            // @ts-ignore
            strapi.io.emit('import:complete', {
                jobId,
                countryId,
                fileType: 'landuse',
                totalFeatures: result.totalFeatures,
                elapsedSeconds,
                featuresPerSecond,
                countryLinkCount,
                regionLinkCount,
            });
            ctx.body = {
                jobId,
                message: 'Landuse import completed successfully',
                countryId,
                fileType: 'landuse',
                result: {
                    totalFeatures: result.totalFeatures,
                    totalBatches: result.totalBatches,
                    elapsedSeconds,
                    featuresPerSecond,
                    countryLinkCount,
                    regionLinkCount,
                },
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            strapi.log.error('Landuse import failed:', error);
            ctx.internalServerError(`Import failed: ${errorMessage}`);
        }
    },
    /**
     * Import building.geojson (building footprints - LARGE FILE)
     * File: sample_data/building.geojson (658MB - requires streaming)
     * Target: building table (needs to be created)
     * NOTE: Table doesn't exist yet - this is a placeholder implementation
     */
    /**
     * Import building.geojson (building footprints for passenger spawning)
     * File: sample_data/building.geojson (100K+ features, 628MB)
     * Target: building table
     * Uses STREAMING parser (memory-efficient for large file)
     */
    async importBuilding(ctx) {
        try {
            const { countryId } = ctx.request.body;
            if (!countryId) {
                return ctx.badRequest('countryId is required');
            }
            // Get the numeric country ID from the document ID using direct SQL
            const knex = strapi.db.connection;
            const countryResult = await knex('countries')
                .select('id')
                .where('document_id', countryId)
                .first();
            if (!countryResult) {
                return ctx.notFound(`Country not found: ${countryId}`);
            }
            const numericCountryId = countryResult.id; // The auto-increment integer ID
            const jobId = `building_${Date.now()}`;
            const startTime = Date.now();
            // Check if file exists
            const geojsonPath = path_1.default.join(process.cwd(), '..', '..', 'sample_data', 'building.geojson');
            if (!fs_1.default.existsSync(geojsonPath)) {
                strapi.log.error(`Building GeoJSON file not found: ${geojsonPath}`);
                return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
            }
            // Get file stats
            const stats = fs_1.default.statSync(geojsonPath);
            const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
            strapi.log.info(`[${jobId}] Starting STREAMING import of ${fileSizeMB} MB file`);
            // Skip estimation for large files - start importing immediately
            const estimatedTotal = 0; // Will be updated as we process
            strapi.log.info(`[${jobId}] Starting import (progress will be tracked without estimation)`);
            // Send initial progress
            // @ts-ignore - Socket.IO instance stored on strapi object
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'building',
                phase: 'starting',
                estimatedTotal,
                fileSizeMB,
            });
            // Stream and process features in batches
            let totalProcessed = 0;
            const result = await (0, geojson_stream_parser_1.streamGeoJSON)(geojsonPath, {
                batchSize: 500,
                onBatch: async (features) => {
                    const knex = strapi.db.connection;
                    const timestamp = new Date();
                    const { randomUUID } = require('crypto');
                    // Build bulk insert values array
                    const insertValues = [];
                    const insertBindings = [];
                    features.forEach((feature) => {
                        const props = feature.properties || {};
                        const buildingName = props.name || `${props.building || 'building'}-${props.osm_id || 'unknown'}`;
                        const buildingId = generateSlug(buildingName, props.osm_id);
                        const documentId = randomUUID(); // Generate UUID for document_id
                        // Convert geometry to WKT
                        let wkt = null;
                        if (feature.geometry) {
                            if (feature.geometry.type === 'Polygon') {
                                const rings = feature.geometry.coordinates;
                                const wktRings = rings.map((ring) => '(' + ring.map((coord) => `${coord[0]} ${coord[1]}`).join(', ') + ')').join(', ');
                                wkt = `POLYGON(${wktRings})`;
                            }
                            else if (feature.geometry.type === 'MultiPolygon') {
                                const polygons = feature.geometry.coordinates;
                                const wktPolygons = polygons.map((rings) => '(' + rings.map((ring) => '(' + ring.map((coord) => `${coord[0]} ${coord[1]}`).join(', ') + ')').join(', ') + ')').join(', ');
                                wkt = `MULTIPOLYGON(${wktPolygons})`;
                            }
                        }
                        insertValues.push('(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?)');
                        insertBindings.push(documentId, // document_id
                        buildingId, // building_id
                        props.osm_id || null, // osm_id
                        props.full_id || null, // full_id
                        props.building || 'yes', // building_type
                        props.name || null, // name
                        props['addr:street'] || null, // addr_street
                        props['addr:city'] || null, // addr_city
                        props['addr:housenumber'] || null, // addr_housenumber
                        props.levels ? parseInt(props.levels) : null, // levels
                        props.height ? parseFloat(props.height) : null, // height
                        props.amenity || null, // amenity
                        wkt, // geom (WKT)
                        timestamp, // created_at
                        timestamp, // updated_at
                        timestamp // published_at
                        );
                    });
                    // Execute bulk insert with geometry in one query
                    if (insertValues.length > 0) {
                        await knex.raw(`
              INSERT INTO buildings (
                document_id, building_id, osm_id, full_id, building_type, name,
                addr_street, addr_city, addr_housenumber, levels, height,
                amenity, geom, created_at, updated_at, published_at
              ) VALUES ${insertValues.join(', ')}
            `, insertBindings);
                        // Link to country (bulk insert into junction table)
                        const buildingIds = await knex('buildings')
                            .select('id')
                            .whereIn('building_id', features.map((f) => {
                            const props = f.properties || {};
                            const buildingName = props.name || `${props.building || 'building'}-${props.osm_id || 'unknown'}`;
                            return generateSlug(buildingName, props.osm_id);
                        }))
                            .orderBy('id', 'desc')
                            .limit(features.length);
                        const countryLinkBindings = [];
                        const countryLinkPlaceholders = buildingIds.map((row) => {
                            countryLinkBindings.push(row.id, numericCountryId);
                            return '(?, ?)';
                        }).join(', ');
                        if (countryLinkPlaceholders) {
                            await knex.raw(`
                INSERT INTO buildings_country_lnk (building_id, country_id)
                VALUES ${countryLinkPlaceholders}
              `, countryLinkBindings);
                        }
                    }
                    totalProcessed += features.length;
                },
                onProgress: (progress) => {
                    // Calculate progress metrics
                    const elapsedSeconds = (progress.elapsedTime / 1000).toFixed(1);
                    const featuresPerSecond = progress.elapsedTime > 0
                        ? (progress.processed / (progress.elapsedTime / 1000)).toFixed(0)
                        : '0';
                    // Calculate percentage and batch info if we have an estimate
                    let progressMessage = `[${jobId}] Progress: ${progress.processed} features`;
                    let percentComplete = '0.0';
                    let estimatedBatches = 0;
                    if (progress.estimatedTotal && progress.estimatedTotal > 0) {
                        percentComplete = ((progress.processed / progress.estimatedTotal) * 100).toFixed(1);
                        estimatedBatches = Math.ceil(progress.estimatedTotal / 500);
                        progressMessage = `[${jobId}] Progress: ${progress.processed}/${progress.estimatedTotal} features (${percentComplete}%)`;
                    }
                    progressMessage += ` | Batch ${progress.currentBatch}`;
                    if (estimatedBatches > 0) {
                        progressMessage += `/${estimatedBatches}`;
                    }
                    progressMessage += ` | ${elapsedSeconds}s elapsed | ${featuresPerSecond} features/sec`;
                    // Emit Socket.IO progress update
                    // @ts-ignore - Socket.IO instance stored on strapi object
                    strapi.io.emit('import:progress', {
                        jobId,
                        countryId,
                        fileType: 'building',
                        processed: progress.processed,
                        estimatedTotal: progress.estimatedTotal,
                        percent: percentComplete,
                        currentBatch: progress.currentBatch,
                        estimatedBatches,
                        elapsedTime: progress.elapsedTime,
                        elapsedSeconds,
                        featuresPerSecond,
                        bytesRead: progress.bytesRead,
                    });
                    // Log progress
                    strapi.log.info(progressMessage);
                },
                onError: (error) => {
                    strapi.log.error(`[${jobId}] Streaming error:`, error);
                    // @ts-ignore - Socket.IO instance stored on strapi object
                    strapi.io.emit('import:error', {
                        jobId,
                        countryId,
                        fileType: 'building',
                        error: error.message,
                    });
                },
            });
            const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
            const featuresPerSecond = (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0);
            const avgBatchTime = (result.elapsedTime / result.totalBatches / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s ` +
                `(${result.totalBatches} batches, ${featuresPerSecond} features/sec, ${avgBatchTime}s/batch)`);
            // Emit completion event
            // @ts-ignore - Socket.IO instance stored on strapi object
            strapi.io.emit('import:complete', {
                jobId,
                countryId,
                fileType: 'building',
                totalFeatures: result.totalFeatures,
                totalBatches: result.totalBatches,
                elapsedTime: result.elapsedTime,
                elapsedSeconds,
                featuresPerSecond,
                avgBatchTime,
            });
            ctx.body = {
                jobId,
                message: 'Building import completed successfully using streaming parser',
                countryId,
                fileType: 'building',
                fileInfo: {
                    path: geojsonPath,
                    sizeMB: fileSizeMB,
                },
                result: {
                    totalFeatures: result.totalFeatures,
                    totalBatches: result.totalBatches,
                    elapsedTime: result.elapsedTime,
                    elapsedSeconds,
                    featuresPerSecond: (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0),
                },
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            strapi.log.error('Building import failed:', error);
            // @ts-ignore - Socket.IO instance stored on strapi object
            strapi.io.emit('import:error', {
                countryId: ctx.request.body.countryId,
                fileType: 'building',
                error: errorMessage,
            });
            ctx.internalServerError(`Import failed: ${errorMessage}`);
        }
    },
    /**
     * Import admin boundaries (regions, parishes, districts)
     * Files: admin_level_6_polygon.geojson (parishes), admin_level_8/9/10 (districts/sub-districts)
     * Target: region table
     */
    async importAdmin(ctx) {
        try {
            const { countryId, adminLevelId, adminLevel } = ctx.request.body;
            if (!countryId) {
                return ctx.badRequest('countryId is required');
            }
            if (!adminLevelId) {
                return ctx.badRequest('adminLevelId is required');
            }
            if (!adminLevel) {
                return ctx.badRequest('adminLevel is required');
            }
            // Get the numeric country ID from the document ID using direct SQL
            const knex = strapi.db.connection;
            const countryResult = await knex('countries')
                .select('id')
                .where('document_id', countryId)
                .first();
            if (!countryResult) {
                return ctx.notFound(`Country not found: ${countryId}`);
            }
            const numericCountryId = countryResult.id;
            // Get the numeric admin_level ID
            const adminLevelResult = await knex('admin_levels')
                .select('id', 'name', 'level')
                .where('id', adminLevelId)
                .first();
            if (!adminLevelResult) {
                return ctx.notFound(`Admin level not found: ${adminLevelId}`);
            }
            const numericAdminLevelId = adminLevelResult.id;
            strapi.log.info(`[Admin Import] Country ID: ${numericCountryId}, Admin Level: ${adminLevelResult.level} (${adminLevelResult.name})`);
            const jobId = `admin_${Date.now()}`;
            const startTime = Date.now();
            // Dynamic file path based on admin level
            const geojsonPath = path_1.default.join(process.cwd(), '..', '..', 'sample_data', `admin_level_${adminLevel}_polygon.geojson`);
            // Check if file exists
            if (!fs_1.default.existsSync(geojsonPath)) {
                strapi.log.error(`Admin GeoJSON file not found: ${geojsonPath}`);
                return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
            }
            // Get file stats
            const stats = fs_1.default.statSync(geojsonPath);
            const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
            strapi.log.info(`[${jobId}] Starting STREAMING import of ${fileSizeMB} MB file (${adminLevelResult.name})`);
            // Send initial progress
            // @ts-ignore - Socket.IO instance stored on strapi object
            strapi.io.emit('import:progress', {
                jobId,
                countryId,
                fileType: 'admin',
                phase: 'starting',
                adminLevel: adminLevelResult.level,
                adminLevelName: adminLevelResult.name,
                fileSizeMB,
            });
            // Stream and process features in batches
            let totalProcessed = 0;
            const result = await (0, geojson_stream_parser_1.streamGeoJSON)(geojsonPath, {
                batchSize: 500,
                onBatch: async (features) => {
                    const knex = strapi.db.connection;
                    const timestamp = new Date();
                    const { randomUUID } = require('crypto');
                    // Build bulk insert values array
                    const insertValues = [];
                    const insertBindings = [];
                    features.forEach((feature) => {
                        const props = feature.properties || {};
                        const regionName = props.name || `admin-${adminLevel}-${props.osm_id || 'unknown'}`;
                        const documentId = randomUUID(); // Generate UUID for document_id
                        // Convert geometry to WKT MultiPolygon and calculate centroid from original coordinates
                        let wkt = null;
                        let centerLat = null;
                        let centerLon = null;
                        if (feature.geometry && (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon')) {
                            let firstRing = [];
                            if (feature.geometry.type === 'MultiPolygon') {
                                // Already MultiPolygon - convert coordinates to WKT
                                const polygons = feature.geometry.coordinates.map((polygon) => {
                                    const rings = polygon.map((ring) => {
                                        const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
                                        return `(${coords})`;
                                    }).join(', ');
                                    return `(${rings})`;
                                }).join(', ');
                                wkt = `MULTIPOLYGON(${polygons})`;
                                // Get first ring for centroid calculation
                                firstRing = feature.geometry.coordinates[0][0];
                            }
                            else {
                                // Convert single Polygon to MultiPolygon for consistency
                                const rings = feature.geometry.coordinates.map((ring) => {
                                    const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
                                    return `(${coords})`;
                                }).join(', ');
                                wkt = `MULTIPOLYGON(((${rings})))`;
                                // Get first ring for centroid calculation
                                firstRing = feature.geometry.coordinates[0];
                            }
                            // Calculate centroid from original GeoJSON coordinates (preserves precision)
                            if (firstRing && firstRing.length > 0) {
                                let sumLat = 0;
                                let sumLon = 0;
                                firstRing.forEach(coord => {
                                    sumLon += coord[0];
                                    sumLat += coord[1];
                                });
                                centerLon = sumLon / firstRing.length;
                                centerLat = sumLat / firstRing.length;
                            }
                        }
                        // Insert with area calculation from geometry
                        insertValues.push('(?, ?, ?, ?, ?, ?, ST_Area(ST_GeomFromText(?, 4326)::geography) / 1000000, ST_GeomFromText(?, 4326), ?, ?, ?)');
                        insertBindings.push(documentId, // document_id
                        props.osm_id || null, // osm_id
                        props.full_id || null, // full_id
                        regionName, // name
                        centerLat, // center_latitude (from original GeoJSON coords)
                        centerLon, // center_longitude (from original GeoJSON coords)
                        wkt, // area_sq_km (calculated from geometry)
                        wkt, // geom (WKT)
                        timestamp, // created_at
                        timestamp, // updated_at
                        timestamp // published_at
                        );
                    });
                    // Execute bulk insert with geometry in one query
                    if (insertValues.length > 0) {
                        await knex.raw(`
                INSERT INTO regions (
                  document_id, osm_id, full_id, name,
                  center_latitude, center_longitude, area_sq_km, geom, created_at, updated_at, published_at
                ) VALUES ${insertValues.join(', ')}
              `, insertBindings);
                        // Get the IDs of the just-inserted regions
                        const regionIds = await knex('regions')
                            .select('id')
                            .whereIn('osm_id', features.map((f) => { var _a; return (_a = f.properties) === null || _a === void 0 ? void 0 : _a.osm_id; }).filter(Boolean))
                            .orderBy('id', 'desc')
                            .limit(features.length);
                        // Link to country (bulk insert into junction table)
                        const countryLinkBindings = [];
                        const countryLinkPlaceholders = regionIds.map((row) => {
                            countryLinkBindings.push(row.id, numericCountryId);
                            return '(?, ?)';
                        }).join(', ');
                        if (countryLinkPlaceholders) {
                            await knex.raw(`
                  INSERT INTO regions_country_lnk (region_id, country_id)
                  VALUES ${countryLinkPlaceholders}
                `, countryLinkBindings);
                        }
                        // Link to admin_level (bulk insert into junction table)
                        const adminLevelLinkBindings = [];
                        const adminLevelLinkPlaceholders = regionIds.map((row) => {
                            adminLevelLinkBindings.push(row.id, numericAdminLevelId);
                            return '(?, ?)';
                        }).join(', ');
                        if (adminLevelLinkPlaceholders) {
                            await knex.raw(`
                  INSERT INTO regions_admin_level_lnk (region_id, admin_level_id)
                  VALUES ${adminLevelLinkPlaceholders}
                `, adminLevelLinkBindings);
                        }
                    }
                    totalProcessed += features.length;
                },
                onProgress: (progress) => {
                    // Calculate progress metrics
                    const elapsedSeconds = (progress.elapsedTime / 1000).toFixed(1);
                    const featuresPerSecond = progress.elapsedTime > 0
                        ? (progress.processed / (progress.elapsedTime / 1000)).toFixed(0)
                        : '0';
                    // Calculate percentage and batch info if we have an estimate
                    let progressMessage = `[${jobId}] Progress: ${progress.processed} features`;
                    let percentComplete = '0.0';
                    let estimatedBatches = 0;
                    if (progress.estimatedTotal && progress.estimatedTotal > 0) {
                        percentComplete = ((progress.processed / progress.estimatedTotal) * 100).toFixed(1);
                        estimatedBatches = Math.ceil(progress.estimatedTotal / 500);
                        progressMessage = `[${jobId}] Progress: ${progress.processed}/${progress.estimatedTotal} features (${percentComplete}%)`;
                    }
                    progressMessage += ` | Batch ${progress.currentBatch}`;
                    if (estimatedBatches > 0) {
                        progressMessage += `/${estimatedBatches}`;
                    }
                    progressMessage += ` | ${elapsedSeconds}s elapsed | ${featuresPerSecond} features/sec`;
                    // Emit Socket.IO progress update
                    // @ts-ignore - Socket.IO instance stored on strapi object
                    strapi.io.emit('import:progress', {
                        jobId,
                        countryId,
                        fileType: 'admin',
                        adminLevel: adminLevelResult.level,
                        adminLevelName: adminLevelResult.name,
                        processed: progress.processed,
                        estimatedTotal: progress.estimatedTotal,
                        percent: percentComplete,
                        currentBatch: progress.currentBatch,
                        estimatedBatches,
                        elapsedTime: progress.elapsedTime,
                        elapsedSeconds,
                        featuresPerSecond,
                        bytesRead: progress.bytesRead,
                    });
                    // Log progress
                    strapi.log.info(progressMessage);
                },
                onError: (error) => {
                    strapi.log.error(`[${jobId}] Streaming error:`, error);
                    // @ts-ignore - Socket.IO instance stored on strapi object
                    strapi.io.emit('import:error', {
                        jobId,
                        countryId,
                        fileType: 'admin',
                        adminLevel: adminLevelResult.level,
                        error: error.message,
                    });
                },
            });
            const elapsedSeconds = ((Date.now() - startTime) / 1000).toFixed(1);
            const featuresPerSecond = (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0);
            const avgBatchTime = (result.elapsedTime / result.totalBatches / 1000).toFixed(1);
            strapi.log.info(`[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s ` +
                `(${result.totalBatches} batches, ${featuresPerSecond} features/sec, ${avgBatchTime}s/batch)`);
            // Emit completion event
            // @ts-ignore - Socket.IO instance stored on strapi object
            strapi.io.emit('import:complete', {
                jobId,
                countryId,
                fileType: 'admin',
                adminLevel: adminLevelResult.level,
                adminLevelName: adminLevelResult.name,
                totalFeatures: result.totalFeatures,
                totalBatches: result.totalBatches,
                elapsedTime: result.elapsedTime,
                elapsedSeconds,
                featuresPerSecond,
                avgBatchTime,
            });
            ctx.body = {
                jobId,
                message: `Admin boundaries import completed successfully using streaming parser`,
                countryId,
                fileType: 'admin',
                adminLevel: adminLevelResult.level,
                adminLevelName: adminLevelResult.name,
                fileInfo: {
                    path: geojsonPath,
                    sizeMB: fileSizeMB,
                },
                result: {
                    totalFeatures: result.totalFeatures,
                    totalBatches: result.totalBatches,
                    elapsedTime: result.elapsedTime,
                    elapsedSeconds,
                    featuresPerSecond: (result.totalFeatures / (result.elapsedTime / 1000)).toFixed(0),
                },
            };
        }
        catch (error) {
            const errorMessage = error instanceof Error ? error.message : 'Unknown error';
            strapi.log.error('Admin import failed:', error);
            // @ts-ignore - Socket.IO instance stored on strapi object
            strapi.io.emit('import:error', {
                countryId: ctx.request.body.countryId,
                fileType: 'admin',
                adminLevel: ctx.request.body.adminLevel,
                error: errorMessage,
            });
            ctx.internalServerError(`Import failed: ${errorMessage}`);
        }
    },
};
//# sourceMappingURL=geojson-import.js.map