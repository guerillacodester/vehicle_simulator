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

        // Create geometry records as individual shape points
        if (firstFeature.geometry && firstFeature.geometry.type === 'LineString') {
          const coordinates = firstFeature.geometry.coordinates;
          
          strapi.log.info(`[${jobId}] Creating geometry with ${coordinates.length} points`);
          
          // Insert each coordinate as a separate highway_shape record
          const shapePointIds: string[] = [];
          for (let i = 0; i < coordinates.length; i++) {
            const [lon, lat] = coordinates[i];
            
            const shapePoint = await strapi.entityService.create('api::highway-shape.highway-shape' as any, {
              data: {
                shape_pt_lat: lat,
                shape_pt_lon: lon,
                shape_pt_sequence: i,
              }
            });
            
            shapePointIds.push(String(shapePoint.id));
          }

          // Create linking table entries to connect shape points to highway
          const knex = strapi.db.connection;
          for (let i = 0; i < shapePointIds.length; i++) {
            await knex.raw(`
              INSERT INTO highway_shapes_highway_lnk (highway_shape_id, highway_id, highway_shape_ord)
              VALUES (?, ?, ?)
            `, [shapePointIds[i], highway.id, i]);
          }

          strapi.log.info(`[${jobId}] Created ${shapePointIds.length} shape points and linked to highway`);
          
          testInsertResult = {
            highwayId: highway.id,
            geometryPointCount: shapePointIds.length,
            osmId: props?.osm_id,
            name: props?.name,
            coordinateCount: coordinates.length,
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

      // TODO: Implement streaming import
      ctx.body = {
        jobId: `amenity_${Date.now()}`,
        message: 'Amenity import started (STUB)',
        countryId,
        fileType: 'amenity',
      };
    } catch (error) {
      strapi.log.error('Amenity import failed:', error);
      ctx.internalServerError('Import failed');
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

      // TODO: Implement streaming import
      ctx.body = {
        jobId: `landuse_${Date.now()}`,
        message: 'Landuse import started (STUB)',
        countryId,
        fileType: 'landuse',
      };
    } catch (error) {
      strapi.log.error('Landuse import failed:', error);
      ctx.internalServerError('Import failed');
    }
  },

  /**
   * Import building.geojson (building footprints - LARGE FILE)
   * File: sample_data/building.geojson (658MB - requires streaming)
   * Target: building table (needs to be created)
   */
  async importBuilding(ctx: any) {
    try {
      const { countryId } = ctx.request.body;

      if (!countryId) {
        return ctx.badRequest('countryId is required');
      }

      // TODO: Implement streaming import with chunking
      ctx.body = {
        jobId: `building_${Date.now()}`,
        message: 'Building import started (STUB - streaming required)',
        countryId,
        fileType: 'building',
      };
    } catch (error) {
      strapi.log.error('Building import failed:', error);
      ctx.internalServerError('Import failed');
    }
  },

    /**
     * Import admin boundaries (regions, parishes, districts)
     * Files: admin_level_6_polygon.geojson (parishes), admin_level_8/9/10 (districts/sub-districts)
     * Target: region table + place table
     */
    async importAdmin(ctx: any) {
      try {
        const { countryId } = ctx.request.body;

        if (!countryId) {
          return ctx.badRequest('countryId is required');
        }

        // TODO: Implement streaming import (multiple files)
        ctx.body = {
          jobId: `admin_${Date.now()}`,
          message: 'Admin boundaries import started (STUB)',
          countryId,
          fileType: 'admin',
        };
      } catch (error) {
        strapi.log.error('Admin import failed:', error);
        ctx.internalServerError('Import failed');
      }
    },
  };
