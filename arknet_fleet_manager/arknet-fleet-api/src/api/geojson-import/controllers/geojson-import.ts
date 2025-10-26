/**
 * GeoJSON Import Controller
 * Handles GeoJSON file imports with streaming parser and Socket.IO progress updates
 */

import fs from 'fs';
import path from 'path';
import { streamGeoJSON, estimateFeatureCount } from '../../../utils/geojson-stream-parser';

// Helper function to generate a slug/UID
function generateSlug(name: string, suffix?: string): string {
  const slug = name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '');
  return suffix ? `${slug}-${suffix}` : slug;
}

export default {
  /**
   * Health check endpoint
   */
  async health(ctx: any) {
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
  async importHighway(ctx: any) {
    try {
      const { countryId } = ctx.request.body;

      if (!countryId) {
        return ctx.badRequest('countryId is required');
      }

      const jobId = `highway_${Date.now()}`;
      
      // Step 1.7.3a: Test file reading and basic parsing
      const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', 'highway.geojson');
      
      // Check if file exists
      if (!fs.existsSync(geojsonPath)) {
        strapi.log.error(`Highway GeoJSON file not found: ${geojsonPath}`);
        return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
      }

      // Get file stats
      const fileStats = fs.statSync(geojsonPath);
      const fileSizeMB = (fileStats.size / (1024 * 1024)).toFixed(2);
      
      strapi.log.info(`[${jobId}] Starting highway import`);
      strapi.log.info(`[${jobId}] File: ${geojsonPath}`);
      strapi.log.info(`[${jobId}] Size: ${fileSizeMB} MB`);
      strapi.log.info(`[${jobId}] Country: ${countryId}`);

      // Read and parse GeoJSON (for testing - will use streaming later)
      const geojsonContent = fs.readFileSync(geojsonPath, 'utf-8');
      const geojson = JSON.parse(geojsonContent);
      
      const featureCount = geojson.features ? geojson.features.length : 0;
      strapi.log.info(`[${jobId}] Features found: ${featureCount}`);
      
      // Step 1.7.3c: Insert first test feature into database
      let testInsertResult = null;
      if (geojson.features && geojson.features.length > 0) {
        const firstFeature = geojson.features[0];
        const propertyKeys = Object.keys(firstFeature.properties || {});
        strapi.log.info(`[${jobId}] Sample feature property count: ${propertyKeys.length}`);
        strapi.log.info(`[${jobId}] Sample feature properties: ${propertyKeys.join(', ')}`);
        strapi.log.info(`[${jobId}] Sample geometry type: ${firstFeature.geometry?.type}`);
        strapi.log.info(`[${jobId}] Sample coordinates count: ${firstFeature.geometry?.coordinates?.length || 0}`);
        
        // Show key properties we'll map to database
        const props = firstFeature.properties;
        strapi.log.info(`[${jobId}] Key mapped properties:`, {
          osm_id: props?.osm_id,
          highway: props?.highway,
          name: props?.name,
          ref: props?.ref,
          surface: props?.surface,
          maxspeed: props?.maxspeed,
          lanes: props?.lanes,
          oneway: props?.oneway,
        });

        // Insert first feature as test
        strapi.log.info(`[${jobId}] Inserting first feature into database...`);
        
        // Create highway record
        // Note: name is required, so we provide a fallback based on osm_id or highway type
        const roadName = props?.name || props?.ref || `${props?.highway || 'road'}-${props?.osm_id || 'unknown'}`;
        
        // Generate highway_id (UID) manually since auto-generation seems to have validation issues
        const highwayId = generateSlug(roadName, props?.osm_id);
        
        const highwayData = {
          highway_id: highwayId,
          osm_id: props?.osm_id || null,
          full_id: props?.full_id || null,
          highway_type: props?.highway || 'other',
          name: roadName,
          ref: props?.ref || null,
          surface: props?.surface || null,
          maxspeed: props?.maxspeed || null,
          lanes: props?.lanes ? parseInt(props.lanes) : null,
          oneway: props?.oneway === 'yes' ? true : (props?.oneway === 'no' ? false : null),
          country: countryId,
        };
        
        strapi.log.info(`[${jobId}] Generated highway_id: ${highwayId}`);

        const highway = await strapi.entityService.create('api::highway.highway' as any, {
          data: highwayData,
        });

        strapi.log.info(`[${jobId}] Highway record created with ID: ${highway.id}`);

        // Create PostGIS geometry
        if (firstFeature.geometry && firstFeature.geometry.type === 'LineString') {
          const coordinates = firstFeature.geometry.coordinates;
          
          strapi.log.info(`[${jobId}] Creating PostGIS geometry with ${coordinates.length} points`);
          
          // Convert coordinates to WKT format for PostGIS
          const wktCoords = coordinates.map((coord: number[]) => `${coord[0]} ${coord[1]}`).join(', ');
          const wkt = `LINESTRING(${wktCoords})`;
          
          // Insert geometry using PostGIS ST_GeomFromText
          const knex = strapi.db.connection;
          await knex.raw(`
            UPDATE highways
            SET geom = ST_GeomFromText(?, 4326)
            WHERE id = ?
          `, [wkt, highway.id]);

          strapi.log.info(`[${jobId}] PostGIS geometry created successfully`);
          
          testInsertResult = {
            highwayId: highway.id,
            geometryPointCount: coordinates.length,
            osmId: props?.osm_id,
            name: props?.name,
            coordinateCount: coordinates.length,
            geometryType: 'LineString',
            usesPostGIS: true,
          };
        }
      }

      ctx.body = {
        jobId,
        message: testInsertResult 
          ? 'Highway import - first test feature inserted successfully' 
          : 'Highway import file validated and parsed successfully',
        countryId,
        fileType: 'highway',
        fileInfo: {
          path: geojsonPath,
          sizeMB: fileSizeMB,
          featureCount,
          geometryType: geojson.type,
        },
        testInsert: testInsertResult,
        nextStep: testInsertResult 
          ? 'Step 1.7.3d: Verify database insertion' 
          : 'Ready for Step 1.7.3c: Insert first test feature into database',
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      strapi.log.error('Highway import failed:', error);
      ctx.internalServerError(`Import failed: ${errorMessage}`);
    }
  },

  /**
   * Import amenity.geojson (POIs for passenger spawning)
   * File: sample_data/amenity.geojson (1,427 features, 3.8MB)
   * Target: poi table
   */
  async importAmenity(ctx: any) {
    try {
      const { countryId } = ctx.request.body;

      if (!countryId) {
        return ctx.badRequest('countryId is required');
      }

      const jobId = `amenity_${Date.now()}`;
      
      // Test file reading and basic parsing
      const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', 'amenity.geojson');
      
      // Check if file exists
      if (!fs.existsSync(geojsonPath)) {
        strapi.log.error(`Amenity GeoJSON file not found: ${geojsonPath}`);
        return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
      }

      // Get file stats
      const stats = fs.statSync(geojsonPath);
      const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      strapi.log.info(`[${jobId}] File found: ${geojsonPath} (${fileSizeMB} MB)`);

      // Read and parse GeoJSON
      const geojsonContent = fs.readFileSync(geojsonPath, 'utf8');
      const geojson = JSON.parse(geojsonContent);
      const featureCount = geojson.features?.length || 0;

      strapi.log.info(`[${jobId}] Parsed ${featureCount} features`);

      // Insert first feature as test
      let testInsertResult = null;
      
      if (featureCount > 0) {
        const firstFeature = geojson.features[0];
        const props = firstFeature.properties;
        
        strapi.log.info(`[${jobId}] Sample feature properties:`, {
          osm_id: props?.osm_id,
          amenity: props?.amenity,
          name: props?.name,
          geometry_type: firstFeature.geometry?.type,
        });

        // Create POI record
        const poiName = props?.name || `${props?.amenity || 'poi'}-${props?.osm_id || 'unknown'}`;
        const poiId = generateSlug(poiName, props?.osm_id);
        
        const poiData = {
          poi_id: poiId,
          osm_id: props?.osm_id || null,
          full_id: props?.full_id || null,
          amenity_type: props?.amenity || 'other',
          name: poiName,
          country: countryId,
        };

        const poi = await strapi.entityService.create('api::poi.poi' as any, {
          data: poiData,
        });

        strapi.log.info(`[${jobId}] POI record created with ID: ${poi.id}`);

        // Create PostGIS Point geometry (extract centroid from MultiPolygon/Polygon)
        if (firstFeature.geometry) {
          let lon: number, lat: number;
          
          // Extract centroid based on geometry type
          if (firstFeature.geometry.type === 'Point') {
            [lon, lat] = firstFeature.geometry.coordinates;
          } else if (firstFeature.geometry.type === 'Polygon') {
            // Calculate centroid of polygon
            const coords = firstFeature.geometry.coordinates[0]; // outer ring
            lon = coords.reduce((sum: number, c: number[]) => sum + c[0], 0) / coords.length;
            lat = coords.reduce((sum: number, c: number[]) => sum + c[1], 0) / coords.length;
          } else if (firstFeature.geometry.type === 'MultiPolygon') {
            // Calculate centroid of first polygon in multipolygon
            const coords = firstFeature.geometry.coordinates[0][0]; // first polygon, outer ring
            lon = coords.reduce((sum: number, c: number[]) => sum + c[0], 0) / coords.length;
            lat = coords.reduce((sum: number, c: number[]) => sum + c[1], 0) / coords.length;
          } else {
            throw new Error(`Unsupported geometry type: ${firstFeature.geometry.type}`);
          }
          
          strapi.log.info(`[${jobId}] Extracted centroid: [${lon}, ${lat}]`);
          
          // Create PostGIS Point geometry
          const wkt = `POINT(${lon} ${lat})`;
          const knex = strapi.db.connection;
          await knex.raw(`
            UPDATE pois
            SET geom = ST_GeomFromText(?, 4326)
            WHERE id = ?
          `, [wkt, poi.id]);

          strapi.log.info(`[${jobId}] PostGIS Point geometry created successfully`);
          
          testInsertResult = {
            poiId: poi.id,
            name: poiName,
            amenityType: props?.amenity,
            centroid: [lon, lat],
            originalGeometryType: firstFeature.geometry.type,
          };
        }
      }

      ctx.body = {
        jobId,
        message: testInsertResult 
          ? 'Amenity import - first test feature inserted successfully with PostGIS Point' 
          : 'Amenity import file validated and parsed successfully',
        countryId,
        fileType: 'amenity',
        fileInfo: {
          path: geojsonPath,
          sizeMB: fileSizeMB,
          featureCount,
          geometryType: geojson.type,
        },
        testInsert: testInsertResult,
      };
    } catch (error) {
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
  async importLanduse(ctx: any) {
    try {
      const { countryId } = ctx.request.body;

      if (!countryId) {
        return ctx.badRequest('countryId is required');
      }

      const jobId = `landuse_${Date.now()}`;
      
      // Test file reading and basic parsing
      const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', 'landuse.geojson');
      
      // Check if file exists
      if (!fs.existsSync(geojsonPath)) {
        strapi.log.error(`Landuse GeoJSON file not found: ${geojsonPath}`);
        return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
      }

      // Get file stats
      const stats = fs.statSync(geojsonPath);
      const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      strapi.log.info(`[${jobId}] File found: ${geojsonPath} (${fileSizeMB} MB)`);

      // Read and parse GeoJSON
      const geojsonContent = fs.readFileSync(geojsonPath, 'utf8');
      const geojson = JSON.parse(geojsonContent);
      const featureCount = geojson.features?.length || 0;

      strapi.log.info(`[${jobId}] Parsed ${featureCount} features`);

      // Insert first feature as test
      let testInsertResult = null;
      
      if (featureCount > 0) {
        const firstFeature = geojson.features[0];
        const props = firstFeature.properties;
        
        strapi.log.info(`[${jobId}] Sample feature properties:`, {
          osm_id: props?.osm_id,
          landuse: props?.landuse,
          name: props?.name,
          geometry_type: firstFeature.geometry?.type,
        });

        // Create landuse_zone record
        const zoneName = props?.name || `${props?.landuse || 'zone'}-${props?.osm_id || 'unknown'}`;
        const zoneId = generateSlug(zoneName, props?.osm_id);
        
        const zoneData = {
          zone_id: zoneId,
          osm_id: props?.osm_id || null,
          full_id: props?.full_id || null,
          landuse_type: props?.landuse || 'other',
          name: zoneName,
          country: countryId,
        };

        const zone = await strapi.entityService.create('api::landuse-zone.landuse-zone' as any, {
          data: zoneData,
        });

        strapi.log.info(`[${jobId}] Landuse zone record created with ID: ${zone.id}`);

        // Create PostGIS Polygon geometry
        if (firstFeature.geometry && (firstFeature.geometry.type === 'Polygon' || firstFeature.geometry.type === 'MultiPolygon')) {
          let wkt: string;
          
          if (firstFeature.geometry.type === 'Polygon') {
            // Convert polygon coordinates to WKT
            const rings = firstFeature.geometry.coordinates.map((ring: number[][]) => {
              const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
              return `(${coords})`;
            }).join(', ');
            wkt = `POLYGON(${rings})`;
          } else {
            // MultiPolygon - convert to Polygon using first polygon
            const firstPolygon = firstFeature.geometry.coordinates[0];
            const rings = firstPolygon.map((ring: number[][]) => {
              const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
              return `(${coords})`;
            }).join(', ');
            wkt = `POLYGON(${rings})`;
            strapi.log.warn(`[${jobId}] Converted MultiPolygon to Polygon (using first polygon only)`);
          }
          
          strapi.log.info(`[${jobId}] Creating PostGIS Polygon geometry`);
          
          // Insert geometry using PostGIS
          const knex = strapi.db.connection;
          await knex.raw(`
            UPDATE landuse_zones
            SET geom = ST_GeomFromText(?, 4326)
            WHERE id = ?
          `, [wkt, zone.id]);

          strapi.log.info(`[${jobId}] PostGIS Polygon geometry created successfully`);
          
          testInsertResult = {
            zoneId: zone.id,
            name: zoneName,
            landuseType: props?.landuse,
            geometryType: firstFeature.geometry.type,
          };
        }
      }

      ctx.body = {
        jobId,
        message: testInsertResult 
          ? 'Landuse import - first test feature inserted successfully with PostGIS Polygon' 
          : 'Landuse import file validated and parsed successfully',
        countryId,
        fileType: 'landuse',
        fileInfo: {
          path: geojsonPath,
          sizeMB: fileSizeMB,
          featureCount,
          geometryType: geojson.type,
        },
        testInsert: testInsertResult,
      };
    } catch (error) {
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
  async importBuilding(ctx: any) {
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
      const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', 'building.geojson');
      
      if (!fs.existsSync(geojsonPath)) {
        strapi.log.error(`Building GeoJSON file not found: ${geojsonPath}`);
        return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
      }

      // Get file stats
      const stats = fs.statSync(geojsonPath);
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
      
      const result = await streamGeoJSON(geojsonPath, {
        batchSize: 500,
        
        onBatch: async (features: any[]) => {
          const knex = strapi.db.connection;
          const timestamp = new Date();
          const { randomUUID } = require('crypto');
          
          // Build bulk insert values array
          const insertValues: any[] = [];
          const insertBindings: any[] = [];
          
          features.forEach((feature: any) => {
            const props = feature.properties || {};
            const buildingName = props.name || `${props.building || 'building'}-${props.osm_id || 'unknown'}`;
            const buildingId = generateSlug(buildingName, props.osm_id);
            const documentId = randomUUID(); // Generate UUID for document_id
            
            // Convert geometry to WKT
            let wkt = null;
            if (feature.geometry) {
              if (feature.geometry.type === 'Polygon') {
                const rings = feature.geometry.coordinates;
                const wktRings = rings.map((ring: number[][]) => 
                  '(' + ring.map((coord: number[]) => `${coord[0]} ${coord[1]}`).join(', ') + ')'
                ).join(', ');
                wkt = `POLYGON(${wktRings})`;
              } else if (feature.geometry.type === 'MultiPolygon') {
                const polygons = feature.geometry.coordinates;
                const wktPolygons = polygons.map((rings: number[][][]) =>
                  '(' + rings.map((ring: number[][]) => 
                    '(' + ring.map((coord: number[]) => `${coord[0]} ${coord[1]}`).join(', ') + ')'
                  ).join(', ') + ')'
                ).join(', ');
                wkt = `MULTIPOLYGON(${wktPolygons})`;
              }
            }
            
            insertValues.push('(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?)');
            insertBindings.push(
              documentId,                                    // document_id
              buildingId,                                    // building_id
              props.osm_id || null,                          // osm_id
              props.full_id || null,                         // full_id
              props.building || 'yes',                       // building_type
              props.name || null,                            // name
              props['addr:street'] || null,                  // addr_street
              props['addr:city'] || null,                    // addr_city
              props['addr:housenumber'] || null,             // addr_housenumber
              props.levels ? parseInt(props.levels) : null,  // levels
              props.height ? parseFloat(props.height) : null,// height
              props.amenity || null,                         // amenity
              wkt,                                           // geom (WKT)
              timestamp,                                     // created_at
              timestamp,                                     // updated_at
              timestamp                                      // published_at
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
              .whereIn('building_id', features.map((f: any) => {
                const props = f.properties || {};
                const buildingName = props.name || `${props.building || 'building'}-${props.osm_id || 'unknown'}`;
                return generateSlug(buildingName, props.osm_id);
              }))
              .orderBy('id', 'desc')
              .limit(features.length);
            
            const countryLinkBindings: any[] = [];
            const countryLinkPlaceholders = buildingIds.map((row: any) => {
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
      
      strapi.log.info(
        `[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s ` +
        `(${result.totalBatches} batches, ${featuresPerSecond} features/sec, ${avgBatchTime}s/batch)`
      );

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
    } catch (error: any) {
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
    async importAdmin(ctx: any) {
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
        const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', `admin_level_${adminLevel}_polygon.geojson`);
        
        // Check if file exists
        if (!fs.existsSync(geojsonPath)) {
          strapi.log.error(`Admin GeoJSON file not found: ${geojsonPath}`);
          return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
        }

        // Get file stats
        const stats = fs.statSync(geojsonPath);
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
        
        const result = await streamGeoJSON(geojsonPath, {
          batchSize: 500,
          
          onBatch: async (features: any[]) => {
            const knex = strapi.db.connection;
            const timestamp = new Date();
            const { randomUUID } = require('crypto');
            
            // Build bulk insert values array
            const insertValues: any[] = [];
            const insertBindings: any[] = [];
            
            features.forEach((feature: any) => {
              const props = feature.properties || {};
              const regionName = props.name || `admin-${adminLevel}-${props.osm_id || 'unknown'}`;
              const documentId = randomUUID(); // Generate UUID for document_id
              
              // Convert geometry to WKT MultiPolygon
              let wkt = null;
              if (feature.geometry && (feature.geometry.type === 'Polygon' || feature.geometry.type === 'MultiPolygon')) {
                if (feature.geometry.type === 'MultiPolygon') {
                  // Already MultiPolygon - convert coordinates to WKT
                  const polygons = feature.geometry.coordinates.map((polygon: number[][][]) => {
                    const rings = polygon.map((ring: number[][]) => {
                      const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
                      return `(${coords})`;
                    }).join(', ');
                    return `(${rings})`;
                  }).join(', ');
                  wkt = `MULTIPOLYGON(${polygons})`;
                } else {
                  // Convert single Polygon to MultiPolygon for consistency
                  const rings = feature.geometry.coordinates.map((ring: number[][]) => {
                    const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
                    return `(${coords})`;
                  }).join(', ');
                  wkt = `MULTIPOLYGON(((${rings})))`;
                }
              }
              
              insertValues.push('(?, ?, ?, ?, ST_GeomFromText(?, 4326), ?, ?, ?)');
              insertBindings.push(
                documentId,                // document_id
                props.osm_id || null,      // osm_id
                props.full_id || null,     // full_id
                regionName,                // name
                wkt,                       // geom (WKT)
                timestamp,                 // created_at
                timestamp,                 // updated_at
                timestamp                  // published_at
              );
            });
            
            // Execute bulk insert with geometry in one query
            if (insertValues.length > 0) {
              await knex.raw(`
                INSERT INTO regions (
                  document_id, osm_id, full_id, name, geom, created_at, updated_at, published_at
                ) VALUES ${insertValues.join(', ')}
              `, insertBindings);
              
              // Get the IDs of the just-inserted regions
              const regionIds = await knex('regions')
                .select('id')
                .whereIn('osm_id', features.map((f: any) => f.properties?.osm_id).filter(Boolean))
                .orderBy('id', 'desc')
                .limit(features.length);
              
              // Link to country (bulk insert into junction table)
              const countryLinkBindings: any[] = [];
              const countryLinkPlaceholders = regionIds.map((row: any) => {
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
              const adminLevelLinkBindings: any[] = [];
              const adminLevelLinkPlaceholders = regionIds.map((row: any) => {
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
        
        strapi.log.info(
          `[${jobId}] ✅ Import COMPLETE: ${result.totalFeatures} features in ${elapsedSeconds}s ` +
          `(${result.totalBatches} batches, ${featuresPerSecond} features/sec, ${avgBatchTime}s/batch)`
        );

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
      } catch (error: any) {
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
