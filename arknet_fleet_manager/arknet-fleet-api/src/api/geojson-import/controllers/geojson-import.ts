/**
 * GeoJSON Import Controller
 * Handles GeoJSON file imports with streaming parser and Socket.IO progress updates
 */

import fs from 'fs';
import path from 'path';

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
  async importBuilding(ctx: any) {
    try {
      const { countryId } = ctx.request.body;

      if (!countryId) {
        return ctx.badRequest('countryId is required');
      }

      const jobId = `building_${Date.now()}`;
      
      // Check if file exists
      const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', 'building.geojson');
      
      if (!fs.existsSync(geojsonPath)) {
        strapi.log.error(`Building GeoJSON file not found: ${geojsonPath}`);
        return ctx.notFound(`GeoJSON file not found at: ${geojsonPath}`);
      }

      // Get file stats (don't read the entire 658MB file!)
      const stats = fs.statSync(geojsonPath);
      const fileSizeMB = (stats.size / (1024 * 1024)).toFixed(2);
      strapi.log.info(`[${jobId}] File found: ${geojsonPath} (${fileSizeMB} MB)`);
      strapi.log.warn(`[${jobId}] Large file detected - streaming parser required`);

      // TODO: Building table needs to be created in Strapi schema first
      // TODO: Implement streaming parser for large file (658MB)
      // Pattern will be:
      // 1. Read file in chunks using stream-json
      // 2. For each building feature:
      //    - Extract properties (osm_id, building type, etc.)
      //    - Convert Polygon coordinates to WKT
      //    - INSERT INTO buildings with ST_GeomFromText('POLYGON(...)', 4326)
      // 3. Use batch inserts for performance (500-1000 at a time)

      ctx.body = {
        jobId,
        message: 'Building import - TABLE NOT CREATED YET',
        countryId,
        fileType: 'building',
        fileInfo: {
          path: geojsonPath,
          sizeMB: fileSizeMB,
        },
        warning: 'Building table does not exist in database yet. Create schema first.',
        nextSteps: [
          '1. Create building content type in Strapi',
          '2. Add geom geometry(Polygon, 4326) column',
          '3. Create GIST spatial index',
          '4. Implement streaming parser for 658MB file',
        ],
      };
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      strapi.log.error('Building import failed:', error);
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
        const { countryId } = ctx.request.body;

        if (!countryId) {
          return ctx.badRequest('countryId is required');
        }

        const jobId = `admin_${Date.now()}`;
        
        // Test with admin_level_6_polygon.geojson (parishes)
        const geojsonPath = path.join(process.cwd(), '..', '..', 'sample_data', 'admin_level_6_polygon.geojson');
        
        // Check if file exists
        if (!fs.existsSync(geojsonPath)) {
          strapi.log.error(`Admin GeoJSON file not found: ${geojsonPath}`);
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
            name: props?.name,
            admin_level: props?.admin_level,
            geometry_type: firstFeature.geometry?.type,
          });

          // Create region record
          const regionName = props?.name || `admin-${props?.admin_level || '6'}-${props?.osm_id || 'unknown'}`;
          const regionId = generateSlug(regionName, props?.osm_id);
          
          const regionData = {
            region_id: regionId,
            osm_id: props?.osm_id || null,
            full_id: props?.full_id || null,
            name: regionName,
            admin_level: props?.admin_level ? parseInt(props.admin_level) : 6,
            country: countryId,
          };

          const region = await strapi.entityService.create('api::region.region' as any, {
            data: regionData,
          });

          strapi.log.info(`[${jobId}] Region record created with ID: ${region.id}`);

          // Create PostGIS MultiPolygon geometry
          if (firstFeature.geometry && (firstFeature.geometry.type === 'Polygon' || firstFeature.geometry.type === 'MultiPolygon')) {
            let wkt: string;
            
            if (firstFeature.geometry.type === 'MultiPolygon') {
              // Convert MultiPolygon coordinates to WKT
              const polygons = firstFeature.geometry.coordinates.map((polygon: number[][][]) => {
                const rings = polygon.map((ring: number[][]) => {
                  const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
                  return `(${coords})`;
                }).join(', ');
                return `(${rings})`;
              }).join(', ');
              wkt = `MULTIPOLYGON(${polygons})`;
            } else {
              // Convert single Polygon to MultiPolygon for consistency
              const rings = firstFeature.geometry.coordinates.map((ring: number[][]) => {
                const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
                return `(${coords})`;
              }).join(', ');
              wkt = `MULTIPOLYGON(((${rings})))`;
              strapi.log.info(`[${jobId}] Converted Polygon to MultiPolygon for consistency`);
            }
            
            strapi.log.info(`[${jobId}] Creating PostGIS MultiPolygon geometry`);
            
            // Insert geometry using PostGIS
            const knex = strapi.db.connection;
            await knex.raw(`
              UPDATE regions
              SET geom = ST_GeomFromText(?, 4326)
              WHERE id = ?
            `, [wkt, region.id]);

            strapi.log.info(`[${jobId}] PostGIS MultiPolygon geometry created successfully`);
            
            testInsertResult = {
              regionId: region.id,
              name: regionName,
              adminLevel: props?.admin_level,
              geometryType: firstFeature.geometry.type,
              convertedTo: 'MultiPolygon',
            };
          }
        }

        ctx.body = {
          jobId,
          message: testInsertResult 
            ? 'Admin boundaries import - first test feature inserted successfully with PostGIS MultiPolygon' 
            : 'Admin boundaries import file validated and parsed successfully',
          countryId,
          fileType: 'admin',
          fileInfo: {
            path: geojsonPath,
            sizeMB: fileSizeMB,
            featureCount,
            geometryType: geojson.type,
          },
          testInsert: testInsertResult,
          note: 'Currently imports admin_level_6_polygon.geojson (parishes). Other admin levels (8/9/10) need separate handling.',
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        strapi.log.error('Admin import failed:', error);
        ctx.internalServerError(`Import failed: ${errorMessage}`);
      }
    },
  };
