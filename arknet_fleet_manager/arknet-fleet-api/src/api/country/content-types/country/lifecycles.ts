import fs from 'fs/promises';
import { existsSync, readFileSync } from 'fs';
import path from 'path';

// Type definitions
interface AmenityMapping {
  [key: string]: string;
}

interface PlaceTypeMapping {
  [key: string]: string;
}

interface LanduseMapping {
  [key: string]: string;
}

export default {
  /**
   * Cascade delete: Remove all related geographic data when country is deleted
   */
  async beforeDelete(event: any) {
    const countryId = event.params.where.id;
    
    console.log(`[Country] Deleting country ${countryId} - cleaning up all related data...`);
    
    try {
      // Delete POIs (cascade will delete poi_shapes via relation)
      const pois = await strapi.entityService.findMany('api::poi.poi' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${pois.length} POIs and their shapes...`);
      for (const poi of pois) {
        await strapi.entityService.delete('api::poi.poi' as any, poi.id);
      }
      
      // Delete Landuse Zones (cascade will delete landuse_shapes via relation)
      const zones = await strapi.entityService.findMany('api::landuse-zone.landuse-zone' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${zones.length} Landuse Zones and their shapes...`);
      for (const zone of zones) {
        await strapi.entityService.delete('api::landuse-zone.landuse-zone' as any, zone.id);
      }
      
      // Delete Highways (cascade will delete highway_shapes via relation)
      const highways = await strapi.entityService.findMany('api::highway.highway' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${highways.length} Highways and their shapes...`);
      for (const highway of highways) {
        await strapi.entityService.delete('api::highway.highway' as any, highway.id);
      }
      
      // Delete Regions (cascade will delete region_shapes via relation)
      const regions = await strapi.entityService.findMany('api::region.region' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${regions.length} Regions and their shapes...`);
      for (const region of regions) {
        await strapi.entityService.delete('api::region.region' as any, region.id);
      }
      
      console.log(`[Country] ✅ Cascade delete complete for all entities and their shapes`);
      
    } catch (error) {
      console.error('[Country] Error during cascade delete:', error);
    }
  },

  /**
   * Track which GeoJSON files have changed
   */
  async beforeUpdate(event: any) {
    debugger; // BREAKPOINT: Country beforeUpdate triggered
    const { data, where } = event.params;
    
    console.log('[Country] ===== BEFORE UPDATE DEBUG =====');
    console.log('[Country] Incoming data keys:', Object.keys(data));
    console.log('[Country] POI file in data:', data.hasOwnProperty('pois_geojson_file') ? data.pois_geojson_file : 'NOT IN DATA');
    console.log('[Country] Places file in data:', data.hasOwnProperty('place_names_geojson_file') ? data.place_names_geojson_file : 'NOT IN DATA');
    console.log('[Country] Landuse file in data:', data.hasOwnProperty('landuse_geojson_file') ? data.landuse_geojson_file : 'NOT IN DATA');
    console.log('[Country] Regions file in data:', data.hasOwnProperty('regions_geojson_file') ? data.regions_geojson_file : 'NOT IN DATA');
    
    // Get the current country record to compare file states
    const currentCountry = await strapi.entityService.findOne('api::country.country' as any, where.id, {
      populate: ['pois_geojson_file', 'place_names_geojson_file', 'landuse_geojson_file', 'regions_geojson_file', 'highways_geojson_file']
    }) as any;
    
    console.log('[Country] Current POI file:', currentCountry?.pois_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.pois_geojson_file, ')');
    console.log('[Country] Current Places file:', currentCountry?.place_names_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.place_names_geojson_file, ')');
    console.log('[Country] Current Landuse file:', currentCountry?.landuse_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.landuse_geojson_file, ')');
    console.log('[Country] Current Regions file:', currentCountry?.regions_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.regions_geojson_file, ')');
    console.log('[Country] Current Highways file:', currentCountry?.highways_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.highways_geojson_file, ')');
    
    // Check if there are actually POIs/Landuse/etc in the database for this country
    try {
      const existingPOIsCount = await strapi.db.query('api::poi.poi').count({ where: { country: where.id } });
      const existingLanduseCount = await strapi.db.query('api::landuse-zone.landuse-zone').count({ where: { country: where.id } });
      const existingRegionsCount = await strapi.db.query('api::region.region').count({ where: { country: where.id } });
      const existingHighwaysCount = await strapi.db.query('api::highway.highway').count({ where: { country: where.id } });
      
      console.log('[Country] Existing data in DB - POIs:', existingPOIsCount, 'Landuse:', existingLanduseCount, 'Regions:', existingRegionsCount, 'Highways:', existingHighwaysCount);
    } catch (error: any) {
      console.log('[Country] Could not check existing data counts:', error?.message || error);
    }
    
    // Track which GeoJSON files are being updated or removed
    event.state = event.state || {};
    
    // More precise change detection - only trigger if file ID actually changed
    const currentPoiFileId = currentCountry?.pois_geojson_file?.id;
    const currentLanduseFileId = currentCountry?.landuse_geojson_file?.id;
    const currentRegionsFileId = currentCountry?.regions_geojson_file?.id;
    const currentHighwaysFileId = currentCountry?.highways_geojson_file?.id;
    
    const newPoiFileId = data.pois_geojson_file?.id || data.pois_geojson_file;
    const newLanduseFileId = data.landuse_geojson_file?.id || data.landuse_geojson_file;
    const newRegionsFileId = data.regions_geojson_file?.id || data.regions_geojson_file;
    const newHighwaysFileId = data.highways_geojson_file?.id || data.highways_geojson_file;
    
    event.state.filesChanged = {
      pois: data.hasOwnProperty('pois_geojson_file') && (currentPoiFileId !== newPoiFileId),
      landuse: data.hasOwnProperty('landuse_geojson_file') && (currentLanduseFileId !== newLanduseFileId),
      regions: data.hasOwnProperty('regions_geojson_file') && (currentRegionsFileId !== newRegionsFileId),
      highways: data.hasOwnProperty('highways_geojson_file') && (currentHighwaysFileId !== newHighwaysFileId)
    };
    
    // Track which files are being removed
    // File is removed if: data contains the field AND it's set to null AND there was a previous file
    event.state.filesRemoved = {
      pois: data.hasOwnProperty('pois_geojson_file') && data.pois_geojson_file === null && !!(currentCountry?.pois_geojson_file?.id || currentCountry?.pois_geojson_file),
      landuse: data.hasOwnProperty('landuse_geojson_file') && data.landuse_geojson_file === null && !!(currentCountry?.landuse_geojson_file?.id || currentCountry?.landuse_geojson_file),
      regions: data.hasOwnProperty('regions_geojson_file') && data.regions_geojson_file === null && !!(currentCountry?.regions_geojson_file?.id || currentCountry?.regions_geojson_file),
      highways: data.hasOwnProperty('highways_geojson_file') && data.highways_geojson_file === null && !!(currentCountry?.highways_geojson_file?.id || currentCountry?.highways_geojson_file)
    };
    
    console.log('[Country] File ID comparison:');
    console.log('  POI: current =', currentPoiFileId, 'new =', newPoiFileId);
    console.log('  Landuse: current =', currentLanduseFileId, 'new =', newLanduseFileId);
    console.log('  Regions: current =', currentRegionsFileId, 'new =', newRegionsFileId);
    console.log('  Highways: current =', currentHighwaysFileId, 'new =', newHighwaysFileId);
    
    console.log('[Country] File changes detected:', event.state.filesChanged);
    console.log('[Country] File removals detected:', event.state.filesRemoved);
    console.log('[Country] ===== END DEBUG =====');
  },

  /**
   * Process all uploaded GeoJSON files
   */
  async afterUpdate(event: any) {
    debugger; // BREAKPOINT: Country afterUpdate triggered
    const { result } = event;
    const filesChanged = event.state?.filesChanged || {};
    const filesRemoved = event.state?.filesRemoved || {};
    
    const importResults = [];
    
    // Delete POIs if file was removed OR if file is set to null and POIs exist
    const shouldDeletePOIs = filesRemoved.pois || (filesChanged.pois && !result.pois_geojson_file);
    if (shouldDeletePOIs) {
      console.log('[Country] POIs GeoJSON file removed or set to null - checking for existing POIs...');
      try {
        // First check how many POIs exist for this country
        const existingPOIs = await strapi.db.query('api::poi.poi').findMany({
          where: { country: result.id }
        });
        
        if (existingPOIs.length > 0) {
          console.log(`[Country] Found ${existingPOIs.length} existing POIs - deleting them...`);
          
          // Use bulk delete for efficiency and transaction safety
          const deletedCount = await strapi.db.query('api::poi.poi').deleteMany({
            where: { country: result.id }
          });
          
          console.log(`[Country] ✅ Deleted ${deletedCount} POIs`);
          importResults.push(`🗑️ Deleted ${deletedCount} POIs`);
        } else {
          console.log('[Country] No POIs found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting POIs:', error);
        importResults.push(`❌ POI deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Delete Landuse zones if file was removed OR if file is set to null and Landuse zones exist
    const shouldDeleteLanduse = filesRemoved.landuse || (filesChanged.landuse && !result.landuse_geojson_file);
    if (shouldDeleteLanduse) {
      console.log('[Country] Landuse GeoJSON file removed or set to null - checking for existing Landuse zones...');
      try {
        // First check how many Landuse zones exist for this country
        const existingLanduse = await strapi.db.query('api::landuse-zone.landuse-zone').findMany({
          where: { country: result.id }
        });
        
        if (existingLanduse.length > 0) {
          console.log(`[Country] Found ${existingLanduse.length} existing Landuse zones - deleting them...`);
          
          const deletedCount = await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
            where: { country: result.id }
          });
          
          console.log(`[Country] ✅ Deleted ${deletedCount} Landuse zones`);
          importResults.push(`🗑️ Deleted ${deletedCount} Landuse zones`);
        } else {
          console.log('[Country] No Landuse zones found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting Landuse zones:', error);
        importResults.push(`❌ Landuse deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Delete Regions if file was removed OR if file is set to null and Regions exist
    const shouldDeleteRegions = filesRemoved.regions || (filesChanged.regions && !result.regions_geojson_file);
    if (shouldDeleteRegions) {
      console.log('[Country] Regions GeoJSON file removed or set to null - checking for existing Regions...');
      try {
        // First check how many Regions exist for this country
        const existingRegions = await strapi.db.query('api::region.region').findMany({
          where: { country: result.id }
        });
        
        if (existingRegions.length > 0) {
          console.log(`[Country] Found ${existingRegions.length} existing Regions - deleting them...`);
          
          const deletedCount = await strapi.db.query('api::region.region').deleteMany({
            where: { country: result.id }
          });
          
          console.log(`[Country] ✅ Deleted ${deletedCount} Regions`);
          importResults.push(`🗑️ Deleted ${deletedCount} Regions`);
        } else {
          console.log('[Country] No Regions found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting Regions:', error);
        importResults.push(`❌ Region deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Delete Highways if file was removed OR if file is set to null and Highways exist
    const shouldDeleteHighways = filesRemoved.highways || (filesChanged.highways && !result.highways_geojson_file);
    if (shouldDeleteHighways) {
      console.log('[Country] Highways GeoJSON file removed or set to null - checking for existing Highways...');
      try {
        // First check how many Highways exist for this country
        const existingHighways = await strapi.db.query('api::highway.highway').findMany({
          where: { country: result.id }
        });
        
        if (existingHighways.length > 0) {
          console.log(`[Country] Found ${existingHighways.length} existing Highways - deleting them and their shapes...`);
          
          // Delete highway-shapes first (child records)
          for (const highway of existingHighways) {
            await strapi.db.query('api::highway-shape.highway-shape').deleteMany({
              where: { highway: highway.id }
            });
          }
          
          // Then delete highways (parent records)
          const deletedCount = await strapi.db.query('api::highway.highway').deleteMany({
            where: { country: result.id }
          });
          
          console.log(`[Country] ✅ Deleted ${deletedCount} Highways and their shapes`);
          importResults.push(`🗑️ Deleted ${deletedCount} Highways and their shapes`);
        } else {
          console.log('[Country] No Highways found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting Highways:', error);
        importResults.push(`❌ Highway deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Process POIs
    if (filesChanged.pois && result.pois_geojson_file) {
      console.log('[Country] Processing POIs GeoJSON file...');
      try {
        await processPOIsGeoJSON(result);
        importResults.push('✅ POIs');
      } catch (error: any) {
        console.error('[Country] Error processing POIs:', error);
        importResults.push(`❌ POIs: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Process Landuse
    if (filesChanged.landuse && result.landuse_geojson_file) {
      console.log('[Country] Processing Landuse GeoJSON file...');
      try {
        await processLanduseGeoJSON(result);
        importResults.push('✅ Landuse');
      } catch (error: any) {
        console.error('[Country] Error processing Landuse:', error);
        importResults.push(`❌ Landuse: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Process Regions
    if (filesChanged.regions && result.regions_geojson_file) {
      console.log('[Country] Processing Regions GeoJSON file...');
      try {
        await processRegionsGeoJSON(result);
        importResults.push('✅ Regions');
      } catch (error: any) {
        console.error('[Country] Error processing Regions:', error);
        importResults.push(`❌ Regions: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Process Highways
    if (filesChanged.highways && result.highways_geojson_file) {
      console.log('[Country] Processing Highways GeoJSON file...');
      try {
        await processHighwaysGeoJSON(result);
        importResults.push('✅ Highways');
      } catch (error: any) {
        console.error('[Country] Error processing Highways:', error);
        importResults.push(`❌ Highways: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Update import status if any files were processed
    if (importResults.length > 0) {
      await strapi.entityService.update('api::country.country' as any, result.id, {
        data: {
          geodata_import_status: `${importResults.join(', ')} at ${new Date().toISOString()}`,
          geodata_last_import: new Date()
        } as any
      });
    }
  }
};

/**
 * Process POIs GeoJSON file and import to database
 */
async function processPOIsGeoJSON(country: any) {
  debugger; // BREAKPOINT: POI processing started
  const file = country.pois_geojson_file;
  
  if (!file) {
    console.log('[Country] No POIs GeoJSON file to process');
    return;
  }
  
  // Read file from uploads directory
  const filePath = path.join(strapi.dirs.static.public, file.url);
  
  if (!existsSync(filePath)) {
    throw new Error(`POIs GeoJSON file not found: ${filePath}`);
  }
  
  const fileContent = readFileSync(filePath, 'utf-8');
  const geojson = JSON.parse(fileContent);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: No features array found');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} POI features...`);
  
  // Clear existing POIs for this country
  const existingPOIs = await strapi.entityService.findMany('api::poi.poi' as any, {
    filters: { country: country.id }
  }) as any[];
  
  console.log(`[Country] Deleting ${existingPOIs.length} existing POIs...`);
  
  for (const poi of existingPOIs) {
    await strapi.entityService.delete('api::poi.poi' as any, poi.id);
  }
  
  // Import POIs in chunks (to avoid timeout)
  const CHUNK_SIZE = 100;
  let importedCount = 0;
  
  for (let i = 0; i < geojson.features.length; i += CHUNK_SIZE) {
    const chunk = geojson.features.slice(i, i + CHUNK_SIZE);
    const poisToCreate = [];
    
    for (const feature of chunk) {
      let lat, lon;
      
      // Handle different geometry types
      if (feature.geometry?.type === 'Point') {
        [lon, lat] = feature.geometry.coordinates;
      } else if (feature.geometry?.type === 'Polygon') {
        // Calculate centroid of polygon
        const coordinates = feature.geometry.coordinates[0]; // Outer ring
        lon = coordinates.reduce((sum: number, p: any) => sum + p[0], 0) / coordinates.length;
        lat = coordinates.reduce((sum: number, p: any) => sum + p[1], 0) / coordinates.length;
      } else if (feature.geometry?.type === 'MultiPolygon') {
        // Calculate centroid of first polygon in multipolygon
        const firstPolygon = feature.geometry.coordinates[0][0]; // First polygon, outer ring
        lon = firstPolygon.reduce((sum: number, p: any) => sum + p[0], 0) / firstPolygon.length;
        lat = firstPolygon.reduce((sum: number, p: any) => sum + p[1], 0) / firstPolygon.length;
      } else {
        // Skip unsupported geometry types
        continue;
      }
      
      const props = feature.properties || {};
      
      // Validate coordinates
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        console.warn(`[Country] Invalid coordinates: [${lon}, ${lat}]`);
        continue;
      }
      
      // Map OSM amenity to POI type
      const poiType = mapAmenityType(props.amenity);
      
      // Debug: Log the mapping for troubleshooting
      if (props.amenity && poiType === 'other') {
        console.log(`[Country] DEBUG: Unmapped amenity type "${props.amenity}" -> defaulting to "other"`);
      }
      
      poisToCreate.push({
        name: props.name || props.amenity || 'Unnamed POI',
        poi_type: poiType,
        latitude: lat,
        longitude: lon,
        osm_id: props.osm_id || props.id,
        amenity: props.amenity,
        tags: props.tags ? JSON.stringify(props.tags) : null,
        spawn_weight: 1.0,
        peak_hour_multiplier: 1.0,
        off_peak_multiplier: 1.0,
        is_active: true,
        country: country.id,
        publishedAt: new Date()
      });
    }
    
    // Bulk create chunk using entityService to properly handle relations
    if (poisToCreate.length > 0) {
      // NOTE: createMany() bypasses Strapi's ORM and doesn't populate junction tables
      // We must use entityService.create() for each POI to establish the country relationship
      for (const poiData of poisToCreate) {
        await strapi.entityService.create('api::poi.poi' as any, {
          data: poiData
        });
      }
      
      importedCount += poisToCreate.length;
      console.log(`[Country] POI import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} POIs`);
  
  return importedCount;
}

/**
 * Helper: Map OSM amenity to POI type
 */
function mapAmenityType(amenity: string): string {
  const mapping: AmenityMapping = {
    // Transit
    'bus_station': 'bus_station',
    'bus_stop': 'bus_station',
    'ferry_terminal': 'ferry_terminal',
    'airport': 'airport',
    
    // Commercial
    'marketplace': 'marketplace',
    'market': 'marketplace',
    'shopping_centre': 'shopping_center',
    'shopping_center': 'shopping_center',
    'mall': 'shopping_center',
    'supermarket': 'shopping_center',
    'shop': 'shopping_center',
    
    // Healthcare
    'hospital': 'hospital',
    'clinic': 'clinic',
    'doctors': 'clinic',
    'pharmacy': 'clinic',
    'dentist': 'clinic',
    
    // Education
    'school': 'school',
    'college': 'university',
    'university': 'university',
    'kindergarten': 'school',
    
    // Religious
    'place_of_worship': 'church',
    'church': 'church',
    'mosque': 'church',
    'temple': 'church',
    'synagogue': 'church',
    
    // Government/Public
    'police': 'government',
    'fire_station': 'government',
    'post_office': 'government',
    'townhall': 'government',
    'courthouse': 'government',
    'embassy': 'government',
    'library': 'government',
    
    // Business
    'bank': 'office',
    'office': 'office',
    'company': 'office',
    
    // Hospitality
    'restaurant': 'restaurant',
    'cafe': 'restaurant',
    'fast_food': 'restaurant',
    'food_court': 'restaurant',
    'bar': 'restaurant',
    'pub': 'restaurant',
    'hotel': 'hotel',
    'motel': 'hotel',
    'guesthouse': 'hotel',
    'hostel': 'hotel',
    
    // Recreation
    'park': 'park',
    'playground': 'park',
    'sports_centre': 'park',
    'stadium': 'park',
    'beach': 'beach',
    
    // Residential/Industrial areas
    'residential': 'residential',
    'industrial': 'industrial',
    'commercial': 'office',
    
    // Fuel and services
    'fuel': 'other',
    'parking': 'other',
    'atm': 'other',
    'community_centre': 'other',
    'social_facility': 'other'
  };
  
  if (!amenity) {
    return 'other';
  }
  
  const key = amenity.toLowerCase().trim();
  return mapping[key] || 'other';
}

/**
 * Process Landuse GeoJSON file and import to database
 */
async function processLanduseGeoJSON(country: any) {
  const file = country.landuse_geojson_file;
  
  if (!file?.url) {
    console.warn('[Country] No Landuse GeoJSON file URL found');
    return 0;
  }
  
  console.log(`[Country] Reading Landuse GeoJSON from: ${file.url}`);
  
  // Read and parse GeoJSON
  const filePath = path.join(strapi.dirs.static.public, file.url);
  const content = await fs.readFile(filePath, 'utf-8');
  const geojson = JSON.parse(content);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: missing features array');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} landuse features...`);
  
  // Delete existing landuse zones for this country
  await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
    where: { country: country.id }
  });
  
  let importedCount = 0;
  const chunkSize = 100;
  
  // Process in chunks
  for (let i = 0; i < geojson.features.length; i += chunkSize) {
    const chunk = geojson.features.slice(i, i + chunkSize);
    const zonesToCreate = [];
    
    for (const feature of chunk) {
      const props = feature.properties || {};
      const coords = feature.geometry?.coordinates;
      
      if (!coords) continue;
      
      // Calculate centroid for polygon/multipolygon
      let lat, lon;
      
      if (feature.geometry.type === 'Polygon' && coords[0]?.length > 0) {
        // Simple centroid: average of all points in outer ring
        const ring = coords[0];
        lat = ring.reduce((sum: number, p: any) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum: number, p: any) => sum + p[0], 0) / ring.length;
      } else if (feature.geometry.type === 'MultiPolygon' && coords[0]?.[0]?.length > 0) {
        // Use first polygon's outer ring
        const ring = coords[0][0];
        lat = ring.reduce((sum: number, p: any) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum: number, p: any) => sum + p[0], 0) / ring.length;
      } else if (feature.geometry.type === 'Point') {
        [lon, lat] = coords;
      } else {
        console.warn(`[Country] Unsupported geometry type: ${feature.geometry.type}`);
        continue;
      }
      
      // Validate coordinates
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        console.warn(`[Country] Invalid coordinates: [${lon}, ${lat}]`);
        continue;
      }
      
      // Map OSM landuse to zone type
      const zoneType = mapLanduseType(props.landuse || props.type);
      
      // Store full geometry as GeoJSON string
      const geometryGeoJSON = JSON.stringify(feature.geometry);
      
      zonesToCreate.push({
        name: props.name || `${zoneType} Zone`,
        zone_type: zoneType,
        center_latitude: lat,
        center_longitude: lon,
        geometry_geojson: geometryGeoJSON,
        osm_id: props.osm_id || props.id,
        tags: props.tags ? JSON.stringify(props.tags) : null,
        spawn_weight: 1.0,
        peak_hour_multiplier: 1.0,
        off_peak_multiplier: 1.0,
        is_active: true,
        country: country.id,
        publishedAt: new Date()
      });
    }
    
    // Create zones individually to establish relationships properly
    // We must use entityService.create() for each zone to establish the country relationship
    for (const zoneData of zonesToCreate) {
      await strapi.entityService.create('api::landuse-zone.landuse-zone' as any, {
        data: zoneData
      });
      
      importedCount++;
    }
    
    if (zonesToCreate.length > 0) {
      console.log(`[Country] Landuse import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Landuse Zones`);
  
  return importedCount;
}

/**
 * Helper: Map OSM landuse to zone type
 */
function mapLanduseType(landuse: string): string {
  const mapping: LanduseMapping = {
    'residential': 'residential',
    'commercial': 'commercial',
    'industrial': 'industrial',
    'retail': 'commercial',
    'education': 'institutional',        // Map education to institutional
    'institutional': 'institutional',
    'recreation_ground': 'recreation',
    'park': 'recreation',
    'grass': 'forest',                   // Map grass to forest (closest match)
    'forest': 'forest',
    'farmland': 'farmland',              // Map to farmland (allowed value)
    'agricultural': 'farmland',          // Map agricultural to farmland
    'construction': 'mixed_use',
    'brownfield': 'mixed_use'
  };
  
  const key = landuse?.toLowerCase();
  return (key && mapping[key]) ? mapping[key] : 'other';  // Use 'other' as fallback
}

/**
 * Process Regions GeoJSON file and import to database
 */
async function processRegionsGeoJSON(country: any) {
  const file = country.regions_geojson_file;
  
  if (!file?.url) {
    console.warn('[Country] No Regions GeoJSON file URL found');
    return 0;
  }
  
  console.log(`[Country] Reading Regions GeoJSON from: ${file.url}`);
  
  // Read and parse GeoJSON
  const filePath = path.join(strapi.dirs.static.public, file.url);
  const content = await fs.readFile(filePath, 'utf-8');
  const geojson = JSON.parse(content);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: missing features array');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} region features...`);
  
  // Delete existing regions for this country
  await strapi.db.query('api::region.region').deleteMany({
    where: { country: country.id }
  });
  
  let importedCount = 0;
  const chunkSize = 50; // Smaller chunks for regions (larger geometries)
  
  // Process in chunks
  for (let i = 0; i < geojson.features.length; i += chunkSize) {
    const chunk = geojson.features.slice(i, i + chunkSize);
    const regionsToCreate = [];
    
    for (const feature of chunk) {
      const props = feature.properties || {};
      const coords = feature.geometry?.coordinates;
      
      if (!coords) continue;
      
      // Calculate centroid
      let lat, lon;
      
      if (feature.geometry.type === 'Polygon' && coords[0]?.length > 0) {
        const ring = coords[0];
        lat = ring.reduce((sum: number, p: any) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum: number, p: any) => sum + p[0], 0) / ring.length;
      } else if (feature.geometry.type === 'MultiPolygon' && coords[0]?.[0]?.length > 0) {
        const ring = coords[0][0];
        lat = ring.reduce((sum: number, p: any) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum: number, p: any) => sum + p[0], 0) / ring.length;
      } else {
        console.warn(`[Country] Unsupported geometry type for region: ${feature.geometry.type}`);
        continue;
      }
      
      // Validate coordinates
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        console.warn(`[Country] Invalid coordinates: [${lon}, ${lat}]`);
        continue;
      }
      
      // Map admin_level to region type
      const regionType = mapRegionType(props.admin_level);
      
      // Store full geometry as GeoJSON string
      const geometryGeoJSON = JSON.stringify(feature.geometry);
      
      regionsToCreate.push({
        name: props.name || `Region ${props.osm_id}`,
        region_type: regionType,
        center_lat: lat,
        center_lon: lon,
        geometry_geojson: geometryGeoJSON,
        osm_id: props.osm_id || props.id,
        admin_level: props.admin_level ? parseInt(props.admin_level) : null,
        population: props.population ? parseInt(props.population) : null,
        tags: props.tags ? JSON.stringify(props.tags) : null,
        country: country.id,
        publishedAt: new Date()
      });
    }
    
    // Bulk create chunk
    if (regionsToCreate.length > 0) {
      await strapi.db.query('api::region.region').createMany({
        data: regionsToCreate
      });
      
      importedCount += regionsToCreate.length;
      console.log(`[Country] Regions import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Regions`);
  
  return importedCount;
}

/**
 * Helper: Map admin_level to region type
 */
function mapRegionType(adminLevel: number | string): string {
  const level = typeof adminLevel === 'string' ? parseInt(adminLevel) : adminLevel;
  
  if (level <= 2) return 'country';
  if (level <= 4) return 'state_province';
  if (level <= 6) return 'district';
  if (level <= 8) return 'municipality';
  if (level <= 10) return 'neighborhood';
  
  return 'other';
}

/**
 * Process Highways GeoJSON file and import to database
 */
async function processHighwaysGeoJSON(country: any) {
  const file = country.highways_geojson_file;
  
  if (!file?.url) {
    console.warn('[Country] No Highways GeoJSON file URL found');
    return 0;
  }
  
  console.log(`[Country] Reading Highways GeoJSON from: ${file.url}`);
  
  // Read and parse GeoJSON
  const filePath = path.join(strapi.dirs.static.public, file.url);
  const content = await fs.readFile(filePath, 'utf-8');
  const geojson = JSON.parse(content);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: missing features array');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} highway features...`);
  
  // Delete existing highways and highway-shapes for this country
  const existingHighways = await strapi.db.query('api::highway.highway').findMany({
    where: { country: country.id }
  });
  
  // Delete highway-shapes first (child records)
  for (const highway of existingHighways) {
    await strapi.db.query('api::highway-shape.highway-shape').deleteMany({
      where: { highway: highway.id }
    });
  }
  
  // Delete highways (parent records)
  await strapi.db.query('api::highway.highway').deleteMany({
    where: { country: country.id }
  });
  
  let importedCount = 0;
  const chunkSize = 50; // Process highways in smaller chunks due to shape complexity
  
  // Helper function to calculate distance between two points (Haversine formula)
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371000; // Earth's radius in meters
    const φ1 = lat1 * Math.PI / 180;
    const φ2 = lat2 * Math.PI / 180;
    const Δφ = (lat2 - lat1) * Math.PI / 180;
    const Δλ = (lon2 - lon1) * Math.PI / 180;
    
    const a = Math.sin(Δφ/2) * Math.sin(Δφ/2) +
              Math.cos(φ1) * Math.cos(φ2) *
              Math.sin(Δλ/2) * Math.sin(Δλ/2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    
    return R * c;
  };
  
  // Process in chunks
  for (let i = 0; i < geojson.features.length; i += chunkSize) {
    const chunk = geojson.features.slice(i, i + chunkSize);
    
    for (const feature of chunk) {
      const props = feature.properties || {};
      const coords = feature.geometry?.coordinates;
      
      if (!coords || feature.geometry?.type !== 'LineString') {
        console.warn(`[Country] Skipping non-LineString highway feature: ${props.full_id || 'unknown'}`);
        continue;
      }
      
      if (!Array.isArray(coords) || coords.length === 0) {
        console.warn(`[Country] Skipping highway with no coordinates: ${props.full_id || 'unknown'}`);
        continue;
      }
      
      // Create the highway parent record
      // Note: highway_id is a UID field that auto-generates from name, so we don't set it manually
      // Provide a fallback name for unnamed highways using full_id or index
      const highwayName = props.name || `Highway ${props.full_id || `unnamed_${i}`}`;
      
      const highway = await strapi.entityService.create('api::highway.highway' as any, {
        data: {
          name: highwayName,
          highway_type: props.highway || 'unclassified',
          osm_id: props.osm_id || null,
          full_id: props.full_id || null,
          surface: props.surface || null,
          lanes: props.lanes ? parseInt(props.lanes) : null,
          maxspeed: props.maxspeed || null,
          oneway: props.oneway === 'yes' ? true : false,
          is_active: true,
          country: country.id,
          region: null, // Could be populated later based on geometry
          publishedAt: new Date()
        }
      }) as any;
      
      // Create highway-shape records for each point in the LineString
      let cumulativeDistance = 0;
      
      for (let j = 0; j < coords.length; j++) {
        const [lon, lat] = coords[j];
        
        // Validate coordinates
        if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
          console.warn(`[Country] Invalid coordinates for highway ${props.full_id}: [${lon}, ${lat}]`);
          continue;
        }
        
        // Calculate distance from previous point
        if (j > 0) {
          const [prevLon, prevLat] = coords[j - 1];
          cumulativeDistance += calculateDistance(prevLat, prevLon, lat, lon);
        }
        
        // Create highway-shape record
        await strapi.entityService.create('api::highway-shape.highway-shape' as any, {
          data: {
            shape_pt_lat: lat,
            shape_pt_lon: lon,
            shape_pt_sequence: j,
            shape_dist_traveled: cumulativeDistance,
            highway: highway.id,
            is_active: true,
            publishedAt: new Date()
          }
        });
      }
      
      importedCount++;
    }
    
    if (chunk.length > 0) {
      console.log(`[Country] Highways import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Highways with their shape points`);
  
  return importedCount;
}
