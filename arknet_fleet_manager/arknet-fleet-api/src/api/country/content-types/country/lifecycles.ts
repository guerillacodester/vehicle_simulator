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

// ============================================================================
// HELPER FUNCTIONS - Must be defined BEFORE export to preserve async context
// ============================================================================

/**
 * Map amenity type from OSM tag to our categorization
 */
const mapAmenityType = (amenity: string): string => {
  const mapping: AmenityMapping = {
    'restaurant': 'food_beverage',
    'cafe': 'food_beverage',
    'fast_food': 'food_beverage',
    'pub': 'food_beverage',
    'bar': 'food_beverage',
    'bank': 'financial',
    'atm': 'financial',
    'hospital': 'healthcare',
    'clinic': 'healthcare',
    'pharmacy': 'healthcare',
    'school': 'education',
    'university': 'education',
    'college': 'education',
    'library': 'education',
    'police': 'public_service',
    'fire_station': 'public_service',
    'post_office': 'public_service',
    'parking': 'transport',
    'fuel': 'transport',
    'bus_station': 'transport',
    'place_of_worship': 'religious',
    'church': 'religious',
    'mosque': 'religious',
    'temple': 'religious',
    'supermarket': 'retail',
    'convenience': 'retail',
    'marketplace': 'retail',
    'hotel': 'accommodation',
    'guesthouse': 'accommodation',
    'hostel': 'accommodation'
  };
  
  const key = amenity.toLowerCase().trim();
  return mapping[key] || 'other';
};

/**
 * Map landuse type from OSM tag to our categorization
 */
const mapLanduseType = (landuse: string): string => {
  const mapping: LanduseMapping = {
    'residential': 'residential',
    'commercial': 'commercial',
    'industrial': 'industrial',
    'retail': 'commercial',
    'farmland': 'farmland',
    'farm': 'farmland',
    'farmyard': 'farmland',
    'forest': 'forest',
    'meadow': 'farmland',
    'grass': 'recreation',
    'recreation_ground': 'recreation',
    'park': 'recreation',
    'cemetery': 'institutional',
    'military': 'institutional',
    'quarry': 'industrial',
    'construction': 'industrial',
    'railway': 'transportation',
    'reservoir': 'water',
    'basin': 'water'
  };
  
  const key = landuse.toLowerCase().trim();
  return mapping[key] || 'other';
};

/**
 * Map region type based on admin level
 */
const mapRegionType = (adminLevel: number | string): string => {
  const level = typeof adminLevel === 'string' ? parseInt(adminLevel) : adminLevel;
  
  if (level <= 2) return 'country';
  if (level <= 4) return 'state';
  if (level <= 6) return 'county';
  if (level <= 8) return 'municipality';
  if (level <= 10) return 'district';
  return 'other';
};

/**
 * Process POIs GeoJSON file and import to database
 */
const processPOIsGeoJSON = async (country: any) => {
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
  
  console.log(`[Country] Deleting ${existingPOIs.length} existing POIs and their shapes...`);
  
  let shapesDeletedCount = 0;
  for (const poi of existingPOIs) {
    try {
      // Find all shape IDs linked to this POI via junction table
      const shapeLinks = await strapi.db.query('api::poi-shape.poi-shape').findMany({
        where: { poi: poi.id },
        select: ['id']
      });
      
      // Delete each shape record
      for (const shape of shapeLinks) {
        await strapi.db.query('api::poi-shape.poi-shape').delete({
          where: { id: shape.id }
        });
        shapesDeletedCount++;
      }
    } catch (err) {
      console.error(`[Country] Error deleting shapes for POI ${poi.id}:`, err);
    }
    
    // Then delete the POI parent record
    await strapi.entityService.delete('api::poi.poi' as any, poi.id);
  }
  
  console.log(`[Country] ✅ Deleted ${existingPOIs.length} POIs with ${shapesDeletedCount} shapes`);
  
  // Import POIs in chunks (to avoid timeout)
  const CHUNK_SIZE = 100;
  let importedCount = 0;
  
  for (let i = 0; i < geojson.features.length; i += CHUNK_SIZE) {
    const chunk = geojson.features.slice(i, i + CHUNK_SIZE);
    
    for (const feature of chunk) {
      let lat, lon;
      let geometryType = feature.geometry?.type;
      
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
        const coordinates = feature.geometry.coordinates[0][0];
        lon = coordinates.reduce((sum: number, p: any) => sum + p[0], 0) / coordinates.length;
        lat = coordinates.reduce((sum: number, p: any) => sum + p[1], 0) / coordinates.length;
      } else {
        console.warn(`[Country] Skipping POI with unsupported geometry type: ${feature.geometry?.type}`);
        continue;
      }
      
      const props = feature.properties || {};
      const amenity = props.amenity || props.type || 'other';
      const name = props.name || `${amenity} at ${lat.toFixed(4)}, ${lon.toFixed(4)}`;
      
      // Create the POI parent record
      const createdPOI = await strapi.entityService.create('api::poi.poi' as any, {
        data: {
          name,
          amenity_type: mapAmenityType(amenity),
          original_amenity_tag: amenity,
          latitude: lat,
          longitude: lon,
          osm_id: props.id || props.osm_id,
          address: props.address || props['addr:full'],
          country: country.id,
          is_active: true,
          publishedAt: new Date()
        }
      }) as any;
      
      // Create POI shape records to store the full geometry
      if (feature.geometry) {
        // Store the complete GeoJSON geometry as a single shape record
        await strapi.db.query('api::poi-shape.poi-shape').create({
          data: {
            poi: createdPOI.id,
            geometry_geojson: JSON.stringify(feature.geometry),
            geometry_type: geometryType,
            publishedAt: new Date()
          }
        });
      }
      
      importedCount++;
    }
    
    if (chunk.length > 0) {
      console.log(`[Country] POI import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} POIs`);
  
  return importedCount;
};

/**
 * Process Landuse GeoJSON file and import to database
 */
const processLanduseGeoJSON = async (country: any) => {
  const file = country.landuse_geojson_file;
  
  console.log('[Country] processLanduseGeoJSON called with file:', file ? 'EXISTS' : 'NULL');
  
  if (!file) {
    console.log('[Country] No Landuse GeoJSON file to process');
    return;
  }
  
  console.log('[Country] Landuse file URL:', file.url);
  const filePath = path.join(strapi.dirs.static.public, file.url);
  
  if (!existsSync(filePath)) {
    throw new Error(`Landuse GeoJSON file not found: ${filePath}`);
  }
  
  const fileContent = readFileSync(filePath, 'utf-8');
  const geojson = JSON.parse(fileContent);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: No features array found');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} Landuse features...`);
  
  // Clear existing Landuse zones for this country
  const existingZones = await strapi.db.query('api::landuse-zone.landuse-zone').findMany({
    where: { country: country.id }
  });
  
  console.log(`[Country] Deleting ${existingZones.length} existing Landuse zones and their shapes...`);
  
  let shapesDeletedCount = 0;
  for (const zone of existingZones) {
    try {
      // Find all shape IDs linked to this Landuse zone via junction table
      const shapeLinks = await strapi.db.query('api::landuse-shape.landuse-shape').findMany({
        where: { landuse_zone: zone.id },
        select: ['id']
      });
      
      // Delete each shape record
      for (const shape of shapeLinks) {
        await strapi.db.query('api::landuse-shape.landuse-shape').delete({
          where: { id: shape.id }
        });
        shapesDeletedCount++;
      }
    } catch (err) {
      console.error(`[Country] Error deleting shapes for Landuse zone ${zone.id}:`, err);
    }
  }
  
  // Then bulk delete Landuse zones
  await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
    where: { country: country.id }
  });
  
  console.log(`[Country] ✅ Deleted ${existingZones.length} Landuse zones with ${shapesDeletedCount} shapes`);
  
  // Import Landuse zones
  const CHUNK_SIZE = 50;
  let importedCount = 0;
  
  for (let i = 0; i < geojson.features.length; i += CHUNK_SIZE) {
    const chunk = geojson.features.slice(i, i + CHUNK_SIZE);
    
    for (const feature of chunk) {
      if (!feature.geometry || (feature.geometry.type !== 'Polygon' && feature.geometry.type !== 'MultiPolygon')) {
        console.warn(`[Country] Skipping Landuse with unsupported geometry type: ${feature.geometry?.type}`);
        continue;
      }
      
      const props = feature.properties || {};
      const landuse = props.landuse || props.type || 'other';
      const name = props.name || `${landuse} zone ${i}`;
      const geometryType = feature.geometry.type;
      
      // Calculate centroid
      let lat, lon;
      if (feature.geometry.type === 'Polygon') {
        const coordinates = feature.geometry.coordinates[0];
        lon = coordinates.reduce((sum: number, p: any) => sum + p[0], 0) / coordinates.length;
        lat = coordinates.reduce((sum: number, p: any) => sum + p[1], 0) / coordinates.length;
      } else {
        const coordinates = feature.geometry.coordinates[0][0];
        lon = coordinates.reduce((sum: number, p: any) => sum + p[0], 0) / coordinates.length;
        lat = coordinates.reduce((sum: number, p: any) => sum + p[1], 0) / coordinates.length;
      }
      
      // Create the Landuse zone parent record
      const createdZone = await strapi.entityService.create('api::landuse-zone.landuse-zone' as any, {
        data: {
          name,
          zone_type: mapLanduseType(landuse),
          geometry_geojson: feature.geometry,
          center_latitude: lat,
          center_longitude: lon,
          osm_id: props.id || props.osm_id,
          country: country.id,
          is_active: true,
          publishedAt: new Date()
        }
      }) as any;
      
      // Create Landuse shape records to store the full geometry
      if (feature.geometry) {
        await strapi.db.query('api::landuse-shape.landuse-shape').create({
          data: {
            landuse_zone: createdZone.id,
            geometry_geojson: JSON.stringify(feature.geometry),
            geometry_type: geometryType,
            publishedAt: new Date()
          }
        });
      }
      
      importedCount++;
    }
    
    if (chunk.length > 0) {
      console.log(`[Country] Landuse import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Landuse zones`);
  
  return importedCount;
};

/**
 * Process Regions GeoJSON file and import to database
 */
const processRegionsGeoJSON = async (country: any) => {
  const file = country.regions_geojson_file;
  
  if (!file?.url) {
    console.log('[Country] No Regions GeoJSON file to process');
    return;
  }
  
  const filePath = path.join(strapi.dirs.static.public, file.url);
  
  if (!existsSync(filePath)) {
    throw new Error(`Regions GeoJSON file not found: ${filePath}`);
  }
  
  const fileContent = readFileSync(filePath, 'utf-8');
  const geojson = JSON.parse(fileContent);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: No features array found');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} Region features...`);
  
  // Clear existing Regions for this country
  const existingRegions = await strapi.db.query('api::region.region').findMany({
    where: { country: country.id }
  });
  
  console.log(`[Country] Deleting ${existingRegions.length} existing Regions and their shapes...`);
  
  let shapesDeletedCount = 0;
  for (const region of existingRegions) {
    try {
      // Find all shape IDs linked to this Region via junction table
      const shapeLinks = await strapi.db.query('api::region-shape.region-shape').findMany({
        where: { region: region.id },
        select: ['id']
      });
      
      // Delete each shape record
      for (const shape of shapeLinks) {
        await strapi.db.query('api::region-shape.region-shape').delete({
          where: { id: shape.id }
        });
        shapesDeletedCount++;
      }
    } catch (err) {
      console.error(`[Country] Error deleting shapes for Region ${region.id}:`, err);
    }
  }
  
  // Then bulk delete Regions
  await strapi.db.query('api::region.region').deleteMany({
    where: { country: country.id }
  });
  
  console.log(`[Country] ✅ Deleted ${existingRegions.length} Regions with ${shapesDeletedCount} shapes`);
  
  // Import Regions
  let importedCount = 0;
  
  for (const feature of geojson.features) {
    if (!feature.geometry || (feature.geometry.type !== 'Polygon' && feature.geometry.type !== 'MultiPolygon')) {
      console.warn(`[Country] Skipping Region with unsupported geometry type: ${feature.geometry?.type}`);
      continue;
    }
    
    const props = feature.properties || {};
    const name = props.name || props.NAME || `Region ${importedCount}`;
    const adminLevel = props.admin_level || props.ADMIN_LEVEL || 8;
    const geometryType = feature.geometry.type;
    
    // Calculate centroid
    let lat, lon;
    if (feature.geometry.type === 'Polygon') {
      const coordinates = feature.geometry.coordinates[0];
      lon = coordinates.reduce((sum: number, p: any) => sum + p[0], 0) / coordinates.length;
      lat = coordinates.reduce((sum: number, p: any) => sum + p[1], 0) / coordinates.length;
    } else {
      const coordinates = feature.geometry.coordinates[0][0];
      lon = coordinates.reduce((sum: number, p: any) => sum + p[0], 0) / coordinates.length;
      lat = coordinates.reduce((sum: number, p: any) => sum + p[1], 0) / coordinates.length;
    }
    
    // Create the Region parent record
    const createdRegion = await strapi.entityService.create('api::region.region' as any, {
      data: {
        name,
        region_type: mapRegionType(adminLevel),
        admin_level: parseInt(adminLevel),
        centroid_latitude: lat,
        centroid_longitude: lon,
        osm_id: props.id || props.osm_id,
        country: country.id,
        is_active: true,
        publishedAt: new Date()
      }
    }) as any;
    
    // Create Region shape records to store the full geometry
    if (feature.geometry) {
      await strapi.db.query('api::region-shape.region-shape').create({
        data: {
          region: createdRegion.id,
          geometry_geojson: JSON.stringify(feature.geometry),
          geometry_type: geometryType,
          publishedAt: new Date()
        }
      });
    }
    
    importedCount++;
    
    if (importedCount % 10 === 0) {
      console.log(`[Country] Region import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Regions`);
  
  return importedCount;
};

/**
 * Process Highways GeoJSON file and import to database
 */
const processHighwaysGeoJSON = async (country: any) => {
  const file = country.highways_geojson_file;
  
  if (!file) {
    console.log('[Country] No Highways GeoJSON file to process');
    return;
  }
  
  const filePath = path.join(strapi.dirs.static.public, file.url);
  
  if (!existsSync(filePath)) {
    throw new Error(`Highways GeoJSON file not found: ${filePath}`);
  }
  
  const fileContent = readFileSync(filePath, 'utf-8');
  const geojson = JSON.parse(fileContent);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: No features array found');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} Highway features...`);
  
  // Check if highways already exist and delete them first
  const existingCount = await strapi.db.connection('highways')
    .join('highways_country_lnk', 'highways.id', 'highways_country_lnk.highway_id')
    .where('highways_country_lnk.country_id', country.id)
    .count('* as count')
    .first() as any;
  
  if (existingCount && Number(existingCount.count) > 0) {
    console.log(`[Country] Found ${existingCount.count} existing highways - deleting before fresh import...`);
    
    // Delete in correct order to respect foreign keys
    await strapi.db.connection.raw(`
      DELETE FROM highway_shapes_highway_lnk 
      WHERE highway_id IN (
        SELECT highway_id FROM highways_country_lnk WHERE country_id = ?
      )
    `, [country.id]);
    
    await strapi.db.connection.raw(`
      DELETE FROM highway_shapes 
      WHERE id NOT IN (SELECT highway_shape_id FROM highway_shapes_highway_lnk)
    `);
    
    await strapi.db.connection.raw(`
      DELETE FROM highways 
      WHERE id IN (SELECT highway_id FROM highways_country_lnk WHERE country_id = ?)
    `, [country.id]);
    
    await strapi.db.connection('highways_country_lnk')
      .where('country_id', country.id)
      .del();
    
    console.log(`[Country] ✅ Deleted ${existingCount.count} existing highways`);
  }
  
  // Haversine distance calculation
  const calculateDistance = (lat1: number, lon1: number, lat2: number, lon2: number): number => {
    const R = 6371000; // Earth's radius in meters
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };
  
  // FULLY OPTIMIZED: Bulk DB insert for highways, shapes, and link tables
  // This avoids EntityService overhead and ensures IDs are consistent
  console.log('[Country] Processing highways (fully optimized bulk approach)...');
  
  const BATCH_SIZE = 100;
  let importedCount = 0;
  const timestamp = new Date();
  
  for (let i = 0; i < geojson.features.length; i += BATCH_SIZE) {
    const batch = geojson.features.slice(i, i + BATCH_SIZE);
    
    const highwaysToInsert: any[] = [];
    const coordsByIndex: any[] = [];
    
    // Prepare highway records
    for (let batchIndex = 0; batchIndex < batch.length; batchIndex++) {
      const feature = batch[batchIndex];
      if (feature.geometry?.type !== 'LineString') continue;
      
      const featureIndex = i + batchIndex;
      const props = feature.properties || {};
      const highwayType = props.highway || 'other';
      const name = props.name || props.ref || `${highwayType}_${featureIndex}`;
      
      const validHighwayType = ['motorway', 'trunk', 'primary', 'secondary', 'tertiary', 
                                'residential', 'service', 'unclassified', 'track', 'path', 
                                'footway', 'cycleway', 'steps', 'pedestrian', 'living_street']
                                .includes(highwayType) ? highwayType : 'other';
      
      const highway_id = `${name}_${featureIndex}_${Date.now()}`
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, '-')
        .substring(0, 255);
      
      const documentId = `hw_${Date.now()}_${featureIndex}`.substring(0, 36);
      
      highwaysToInsert.push({
        document_id: documentId,
        highway_id,
        name: name.substring(0, 255),
        highway_type: validHighwayType,
        osm_id: props.id || props.osm_id,
        full_id: props.full_id,
        ref: props.ref ? props.ref.substring(0, 50) : null,
        is_active: true,
        created_at: timestamp,
        updated_at: timestamp,
        published_at: timestamp,
        created_by_id: null,
        updated_by_id: null,
        locale: null
      });
      
      coordsByIndex.push({ coords: feature.geometry.coordinates, documentId });
    }
    
    // Bulk insert highways
    const insertedHighways = await strapi.db.connection('highways')
      .insert(highwaysToInsert)
      .returning(['id', 'document_id']);
    
    console.log(`[Country] Inserted ${insertedHighways.length} highways in batch`);
    
    // Create document_id to numeric id map
    const docIdToNumericId: Record<string, number> = {};
    for (const hw of insertedHighways) {
      docIdToNumericId[hw.document_id] = hw.id;
    }
    
    // Bulk insert country link table entries for highways
    const countryLinks = insertedHighways.map(hw => ({
      highway_id: hw.id,
      country_id: country.id
    }));
    await strapi.db.connection('highways_country_lnk').insert(countryLinks);
    
    // Prepare shapes
    const shapesToInsert: any[] = [];
    const linksToInsert: any[] = [];
    
    for (const { coords, documentId } of coordsByIndex) {
      const numericId = docIdToNumericId[documentId];
      if (!numericId) continue;
      
      for (let j = 0; j < coords.length; j++) {
        const [lon, lat] = coords[j];
        const shapeDocId = `hs_${numericId}_${j}`.substring(0, 36);
        
        shapesToInsert.push({
          document_id: shapeDocId,
          shape_pt_lat: lat,
          shape_pt_lon: lon,
          shape_pt_sequence: j,
          published_at: timestamp,
          created_at: timestamp,
          updated_at: timestamp,
          created_by_id: null,
          updated_by_id: null,
          locale: null
        });
      }
    }
    
    // Bulk insert shapes
    if (shapesToInsert.length > 0) {
      const insertedShapes = await strapi.db.connection('highway_shapes')
        .insert(shapesToInsert)
        .returning(['id', 'document_id']);
      
      console.log(`[Country] Inserted ${insertedShapes.length} shapes`);
      
      // Create link table entries
      for (const { documentId } of coordsByIndex) {
        const numericId = docIdToNumericId[documentId];
        if (!numericId) continue;
        
        const highwayShapes = insertedShapes.filter(s => 
          s.document_id.startsWith(`hs_${numericId}_`)
        );
        
        for (const shape of highwayShapes) {
          linksToInsert.push({
            highway_shape_id: shape.id,
            highway_id: numericId
          });
        }
      }
      
      // Bulk insert link table entries
      if (linksToInsert.length > 0) {
        await strapi.db.connection('highway_shapes_highway_lnk').insert(linksToInsert);
        console.log(`[Country] Inserted ${linksToInsert.length} link table entries`);
      }
    }
    
    importedCount += insertedHighways.length;
    console.log(`[Country] Highway import progress: ${importedCount}/${geojson.features.length}`);
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Highways`);
  return importedCount;
};

// ============================================================================
// LIFECYCLE HOOKS EXPORT
// ============================================================================

export default {
  /**
   * Cascade delete: Remove all related geographic data when country is deleted
   */
  async beforeDelete(event: any) {
    const countryId = event.params.where.id;
    
    console.log(`[Country] Deleting country ${countryId} - cleaning up all related data...`);
    
    try {
      // Delete POIs and their shapes explicitly
      const pois = await strapi.entityService.findMany('api::poi.poi' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${pois.length} POIs and their shapes...`);
      let shapesDeletedCount = 0;
      for (const poi of pois) {
        try {
          // Find all shape IDs linked to this POI via junction table
          const shapeLinks = await strapi.db.query('api::poi-shape.poi-shape').findMany({
            where: { poi: poi.id },
            select: ['id']
          });
          
          // Delete each shape record
          for (const shape of shapeLinks) {
            await strapi.db.query('api::poi-shape.poi-shape').delete({
              where: { id: shape.id }
            });
            shapesDeletedCount++;
          }
        } catch (err) {
          console.error(`[Country] Error deleting shapes for POI ${poi.id}:`, err);
        }
        // Then delete POI parent
        await strapi.entityService.delete('api::poi.poi' as any, poi.id);
      }
      console.log(`[Country] ✅ Deleted ${pois.length} POIs with ${shapesDeletedCount} shapes`);
      
      // Delete Landuse Zones and their shapes
      const zones = await strapi.entityService.findMany('api::landuse-zone.landuse-zone' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${zones.length} Landuse Zones and their shapes...`);
      let zoneshapesDeletedCount = 0;
      for (const zone of zones) {
        try {
          // Query shapes related to this zone through the junction table
          const shapeLinks = await strapi.db.query('api::landuse-shape.landuse-shape').findMany({
            where: { landuse_zone: zone.id },
            select: ['id']
          });
          
          // Delete each shape record
          for (const shape of shapeLinks) {
            await strapi.db.query('api::landuse-shape.landuse-shape').delete({
              where: { id: shape.id }
            });
            zoneshapesDeletedCount++;
          }
        } catch (err) {
          console.error(`[Country] Error deleting shapes for Landuse Zone ${zone.id}:`, err);
        }
        await strapi.entityService.delete('api::landuse-zone.landuse-zone' as any, zone.id);
      }
      console.log(`[Country] ✅ Deleted ${zones.length} Landuse Zones with ${zoneshapesDeletedCount} shapes`);
      
      // Delete Highways and their shapes
      const highways = await strapi.entityService.findMany('api::highway.highway' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${highways.length} Highways and their shapes...`);
      let highwayShapesDeletedCount = 0;
      for (const highway of highways) {
        try {
          // Find shape IDs from link table
          const shapeLinks = await strapi.db.connection('highway_shapes_highway_lnk')
            .select('highway_shape_id')
            .where('highway_id', highway.id);
          
          const shapeIds = shapeLinks.map(link => link.highway_shape_id);
          
          if (shapeIds.length > 0) {
            // Delete shapes
            await strapi.db.connection('highway_shapes')
              .whereIn('id', shapeIds)
              .del();
            highwayShapesDeletedCount += shapeIds.length;
            
            // Delete link table entries
            await strapi.db.connection('highway_shapes_highway_lnk')
              .where('highway_id', highway.id)
              .del();
          }
        } catch (err) {
          console.error(`[Country] Error deleting shapes for Highway ${highway.id}:`, err);
        }
        await strapi.entityService.delete('api::highway.highway' as any, highway.id);
      }
      console.log(`[Country] ✅ Deleted ${highways.length} Highways with ${highwayShapesDeletedCount} shapes`);
      
      // Delete Regions and their shapes
      const regions = await strapi.entityService.findMany('api::region.region' as any, {
        filters: { country: countryId }
      }) as any[];
      console.log(`[Country] Deleting ${regions.length} Regions and their shapes...`);
      let regionShapesDeletedCount = 0;
      for (const region of regions) {
        try {
          // Query shapes related to this region through the junction table
          const shapeLinks = await strapi.db.query('api::region-shape.region-shape').findMany({
            where: { region: region.id },
            select: ['id']
          });
          
          // Delete each shape record
          for (const shape of shapeLinks) {
            await strapi.db.query('api::region-shape.region-shape').delete({
              where: { id: shape.id }
            });
            regionShapesDeletedCount++;
          }
        } catch (err) {
          console.error(`[Country] Error deleting shapes for Region ${region.id}:`, err);
        }
        await strapi.entityService.delete('api::region.region' as any, region.id);
      }
      console.log(`[Country] ✅ Deleted ${regions.length} Regions with ${regionShapesDeletedCount} shapes`);

      
      console.log(`[Country] ✅ Cascade delete complete for all entities and their shapes`);
      
    } catch (error) {
      console.error('[Country] Error during cascade delete:', error);
    }
  },

  /**
   * Track which GeoJSON files have changed
   */
  async beforeUpdate(event: any) {
    try {
      debugger; // BREAKPOINT: Country beforeUpdate triggered
      const { data, where } = event.params;
      
      console.log('[Country] ===== BEFORE UPDATE DEBUG =====');
      console.log('[Country] Incoming data keys:', Object.keys(data));
      console.log('[Country] POI file in data:', data.hasOwnProperty('pois_geojson_file') ? data.pois_geojson_file : 'NOT IN DATA');
      console.log('[Country] Places file in data:', data.hasOwnProperty('place_names_geojson_file') ? data.place_names_geojson_file : 'NOT IN DATA');
      console.log('[Country] Landuse file in data:', data.hasOwnProperty('landuse_geojson_file') ? data.landuse_geojson_file : 'NOT IN DATA');
      console.log('[Country] Regions file in data:', data.hasOwnProperty('regions_geojson_file') ? data.regions_geojson_file : 'NOT IN DATA');
      console.log('[Country] Highways file in data:', data.hasOwnProperty('highways_geojson_file') ? data.highways_geojson_file : 'NOT IN DATA');
      
      // DEBUG: Check relation field formats
      console.log('[Country] DEBUG - Relation field types:');
      console.log('  pois type:', typeof data.pois, 'isArray:', Array.isArray(data.pois), 'value:', data.pois);
      console.log('  landuse_zones type:', typeof data.landuse_zones, 'isArray:', Array.isArray(data.landuse_zones), 'value:', data.landuse_zones);
      console.log('  regions type:', typeof data.regions, 'isArray:', Array.isArray(data.regions), 'value:', data.regions);
      console.log('  highways type:', typeof data.highways, 'isArray:', Array.isArray(data.highways), 'value:', data.highways);
    
      console.log('[Country] Attempting to fetch current country with where:', where);
    
    // Get the current country record to compare file states
    // In Strapi v5, use documentId instead of id
    const countryId = where.documentId || where.id;
    console.log('[Country] Using country identifier:', countryId);
    
    const currentCountry = await strapi.documents('api::country.country').findOne({
      documentId: countryId,
      populate: ['pois_geojson_file', 'landuse_geojson_file', 'regions_geojson_file', 'highways_geojson_file'] as any
    }) as any;
    
    console.log('[Country] Current POI file:', currentCountry?.pois_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.pois_geojson_file, ')');
    console.log('[Country] Current Places file:', currentCountry?.place_names_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.place_names_geojson_file, ')');
    console.log('[Country] Current Landuse file:', currentCountry?.landuse_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.landuse_geojson_file, ')');
    console.log('[Country] Current Regions file:', currentCountry?.regions_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.regions_geojson_file, ')');
    console.log('[Country] Current Highways file:', currentCountry?.highways_geojson_file?.id || 'NONE', '(full object exists:', !!currentCountry?.highways_geojson_file, ')');
    
    // Check if there are actually POIs/Landuse/etc in the database for this country
    // Use the internal ID for database queries, not documentId
    const internalId = currentCountry?.id;
    console.log('[Country] Country internal ID for DB queries:', internalId);
    
    try {
      const existingPOIsCount = await strapi.db.query('api::poi.poi').count({ where: { country: internalId } });
      const existingLanduseCount = await strapi.db.query('api::landuse-zone.landuse-zone').count({ where: { country: internalId } });
      const existingRegionsCount = await strapi.db.query('api::region.region').count({ where: { country: internalId } });
      const existingHighwaysCount = await strapi.db.query('api::highway.highway').count({ where: { country: internalId } });
      
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
    
    // Extract new file IDs - handle both object and direct ID
    // Only extract if field is present in the update data
    const newPoiFileId = data.hasOwnProperty('pois_geojson_file') 
      ? (typeof data.pois_geojson_file === 'object' && data.pois_geojson_file !== null ? data.pois_geojson_file.id : data.pois_geojson_file)
      : currentPoiFileId; // If field not in update, assume no change
    
    const newLanduseFileId = data.hasOwnProperty('landuse_geojson_file')
      ? (typeof data.landuse_geojson_file === 'object' && data.landuse_geojson_file !== null ? data.landuse_geojson_file.id : data.landuse_geojson_file)
      : currentLanduseFileId;
    
    const newRegionsFileId = data.hasOwnProperty('regions_geojson_file')
      ? (typeof data.regions_geojson_file === 'object' && data.regions_geojson_file !== null ? data.regions_geojson_file.id : data.regions_geojson_file)
      : currentRegionsFileId;
    
    const newHighwaysFileId = data.hasOwnProperty('highways_geojson_file')
      ? (typeof data.highways_geojson_file === 'object' && data.highways_geojson_file !== null ? data.highways_geojson_file.id : data.highways_geojson_file)
      : currentHighwaysFileId;
    
    console.log('[Country] DEBUG - New file ID extraction:');
    console.log('  pois_geojson_file in data?', data.hasOwnProperty('pois_geojson_file'));
    console.log('  landuse_geojson_file in data?', data.hasOwnProperty('landuse_geojson_file'));
    console.log('  regions_geojson_file in data?', data.hasOwnProperty('regions_geojson_file'));
    console.log('  highways_geojson_file in data?', data.hasOwnProperty('highways_geojson_file'));
    
    event.state.filesChanged = {
      pois: data.hasOwnProperty('pois_geojson_file') && currentPoiFileId !== newPoiFileId,
      landuse: data.hasOwnProperty('landuse_geojson_file') && currentLanduseFileId !== newLanduseFileId,
      regions: data.hasOwnProperty('regions_geojson_file') && currentRegionsFileId !== newRegionsFileId,
      highways: data.hasOwnProperty('highways_geojson_file') && currentHighwaysFileId !== newHighwaysFileId
    };
    
    // Track which files are being removed
    // File is removed if: field is in update data AND new value is null AND there was a previous file
    event.state.filesRemoved = {
      pois: data.hasOwnProperty('pois_geojson_file') && newPoiFileId === null && currentPoiFileId !== null && currentPoiFileId !== undefined,
      landuse: data.hasOwnProperty('landuse_geojson_file') && newLanduseFileId === null && currentLanduseFileId !== null && currentLanduseFileId !== undefined,
      regions: data.hasOwnProperty('regions_geojson_file') && newRegionsFileId === null && currentRegionsFileId !== null && currentRegionsFileId !== undefined,
      highways: data.hasOwnProperty('highways_geojson_file') && newHighwaysFileId === null && currentHighwaysFileId !== null && currentHighwaysFileId !== undefined
    };
    
    console.log('[Country] File ID comparison:');
    console.log('  POI: current =', currentPoiFileId, 'new =', newPoiFileId);
    console.log('  Landuse: current =', currentLanduseFileId, 'new =', newLanduseFileId);
    console.log('  Regions: current =', currentRegionsFileId, 'new =', newRegionsFileId);
    console.log('  Highways: current =', currentHighwaysFileId, 'new =', newHighwaysFileId);
    
    console.log('[Country] File changes detected:', event.state.filesChanged);
    console.log('[Country] File removals detected:', event.state.filesRemoved);
    console.log('[Country] ===== END DEBUG =====');
    } catch (error: any) {
      console.error('[Country] ❌ ERROR in beforeUpdate:', error);
      console.error('[Country] Error stack:', error?.stack);
      throw error;
    }
  },

  /**
   * Process all uploaded GeoJSON files
   */
  async afterUpdate(event: any) {
    console.log('[Country] ===== AFTER UPDATE STARTED =====');
    debugger; // BREAKPOINT: Country afterUpdate triggered
    
    try {
      const { result } = event;
      
      // CRITICAL: Only process if beforeUpdate set the state
      // This prevents processing on read operations or other non-update events
      if (!event.state || !event.state.filesChanged) {
        console.log('[Country] ⚠️ No filesChanged state found - skipping afterUpdate processing (likely a read operation)');
        return;
      }
      
      const filesChanged = event.state.filesChanged;
      const filesRemoved = event.state.filesRemoved || {};
      
      console.log('[Country] AfterUpdate - filesChanged:', filesChanged);
      console.log('[Country] AfterUpdate - filesRemoved:', filesRemoved);
      console.log('[Country] AfterUpdate - result ID:', result.id);
      console.log('[Country] AfterUpdate - result documentId:', result.documentId);
      
      // CRITICAL FIX: Re-fetch country with populated file fields
      // The result object doesn't include populated relations by default in Strapi v5
      const countryWithFiles = await strapi.documents('api::country.country').findOne({
        documentId: result.documentId,
        populate: ['pois_geojson_file', 'landuse_geojson_file', 'regions_geojson_file', 'highways_geojson_file'] as any
      }) as any;

      // Diagnostic: write a debug file so we can inspect what afterUpdate saw at runtime
      try {
        const debugPayload = {
          ts: new Date().toISOString(),
          result: { id: result.id, documentId: result.documentId },
          filesChanged,
          filesRemoved,
          countryWithFiles: {
            id: countryWithFiles?.id,
            documentId: countryWithFiles?.documentId,
            highways_geojson_file_id: countryWithFiles?.highways_geojson_file?.id || null,
            highways_geojson_file_obj: countryWithFiles?.highways_geojson_file ? true : false
          }
        };
        const debugPath = path.join(strapi.dirs.static.public, 'import_debug_highways.json');
        await fs.writeFile(debugPath, JSON.stringify(debugPayload, null, 2), 'utf-8');
        console.log('[Country] Wrote debug file to', debugPath);
      } catch (dbgErr: any) {
        console.warn('[Country] Failed to write debug file:', dbgErr?.message || dbgErr);
      }
      
      console.log('[Country] Re-fetched country with files:');
      console.log('  POI file:', countryWithFiles?.pois_geojson_file?.id || 'NONE');
      console.log('  Landuse file:', countryWithFiles?.landuse_geojson_file?.id || 'NONE');
      console.log('  Regions file:', countryWithFiles?.regions_geojson_file?.id || 'NONE');
      console.log('  Highways file:', countryWithFiles?.highways_geojson_file?.id || 'NONE');
      
      // Use the re-fetched country for all subsequent processing
      const countryData = { ...result, ...countryWithFiles };
      
      const importResults = [];
    
    // Delete POIs if file was removed OR if file is set to null and POIs exist
    const shouldDeletePOIs = filesRemoved.pois || (filesChanged.pois && !countryData.pois_geojson_file);
    console.log('[Country] shouldDeletePOIs:', shouldDeletePOIs, '(filesRemoved.pois:', filesRemoved.pois, ', filesChanged.pois:', filesChanged.pois, ', has file:', !!countryData.pois_geojson_file, ')');
    if (shouldDeletePOIs) {
      console.log('[Country] POIs GeoJSON file removed or set to null - checking for existing POIs...');
      try {
        // First check how many POIs exist for this country
        const existingPOIs = await strapi.db.query('api::poi.poi').findMany({
          where: { country: countryData.id }
        });
        
        if (existingPOIs.length > 0) {
          console.log(`[Country] Found ${existingPOIs.length} existing POIs - deleting them and their shapes...`);
          
          // Delete POI shapes via junction table - get all shape IDs linked to these POIs
          let shapesDeletedCount = 0;
          for (const poi of existingPOIs) {
            try {
              // Find all shape IDs linked to this POI via junction table
              const shapeLinks = await strapi.db.query('api::poi-shape.poi-shape').findMany({
                where: { poi: poi.id },
                select: ['id']
              });
              
              // Delete each shape record
              for (const shape of shapeLinks) {
                await strapi.db.query('api::poi-shape.poi-shape').delete({
                  where: { id: shape.id }
                });
                shapesDeletedCount++;
              }
            } catch (err) {
              console.error(`[Country] Error deleting shapes for POI ${poi.id}:`, err);
            }
          }
          console.log(`[Country] Deleted ${shapesDeletedCount} POI shapes`);
          
          // Then bulk delete POIs (parent records)
          await strapi.db.query('api::poi.poi').deleteMany({
            where: { country: countryData.id }
          });
          
          console.log(`[Country] ✅ Deleted ${existingPOIs.length} POIs with their shapes`);
          importResults.push(`🗑️ Deleted ${existingPOIs.length} POIs`);
        } else {
          console.log('[Country] No POIs found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting POIs:', error);
        console.error('[Country] Error stack:', error?.stack);
        importResults.push(`❌ POI deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Delete Landuse zones if file was removed OR if file is set to null and Landuse zones exist
    const shouldDeleteLanduse = filesRemoved.landuse || (filesChanged.landuse && !countryData.landuse_geojson_file);
    if (shouldDeleteLanduse) {
      console.log('[Country] Landuse GeoJSON file removed or set to null - checking for existing Landuse zones...');
      try {
        // First check how many Landuse zones exist for this country
        const existingLanduse = await strapi.db.query('api::landuse-zone.landuse-zone').findMany({
          where: { country: countryData.id }
        });
        
        if (existingLanduse.length > 0) {
          console.log(`[Country] Found ${existingLanduse.length} existing Landuse zones - deleting them and their shapes...`);
          
          // Delete Landuse shapes via junction table
          let shapesDeletedCount = 0;
          for (const zone of existingLanduse) {
            try {
              // Find all shape IDs linked to this Landuse zone via junction table
              const shapeLinks = await strapi.db.query('api::landuse-shape.landuse-shape').findMany({
                where: { landuse_zone: zone.id },
                select: ['id']
              });
              
              // Delete each shape record
              for (const shape of shapeLinks) {
                await strapi.db.query('api::landuse-shape.landuse-shape').delete({
                  where: { id: shape.id }
                });
                shapesDeletedCount++;
              }
            } catch (err) {
              console.error(`[Country] Error deleting shapes for Landuse zone ${zone.id}:`, err);
            }
          }
          console.log(`[Country] Deleted ${shapesDeletedCount} Landuse shapes`);
          
          // Then bulk delete Landuse zones (parent records)
          await strapi.db.query('api::landuse-zone.landuse-zone').deleteMany({
            where: { country: countryData.id }
          });
          
          console.log(`[Country] ✅ Deleted ${existingLanduse.length} Landuse zones with their shapes`);
          importResults.push(`🗑️ Deleted ${existingLanduse.length} Landuse zones`);
        } else {
          console.log('[Country] No Landuse zones found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting Landuse zones:', error);
        console.error('[Country] Error stack:', error?.stack);
        importResults.push(`❌ Landuse deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Delete Regions if file was removed OR if file is set to null and Regions exist
    const shouldDeleteRegions = filesRemoved.regions || (filesChanged.regions && !countryData.regions_geojson_file);
    if (shouldDeleteRegions) {
      console.log('[Country] Regions GeoJSON file removed or set to null - checking for existing Regions...');
      try {
        // First check how many Regions exist for this country
        const existingRegions = await strapi.db.query('api::region.region').findMany({
          where: { country: result.id }
        });
        
        if (existingRegions.length > 0) {
          console.log(`[Country] Found ${existingRegions.length} existing Regions - deleting them and their shapes...`);
          
          // Delete Region shapes via junction table
          let shapesDeletedCount = 0;
          for (const region of existingRegions) {
            try {
              // Find all shape IDs linked to this Region via junction table
              const shapeLinks = await strapi.db.query('api::region-shape.region-shape').findMany({
                where: { region: region.id },
                select: ['id']
              });
              
              // Delete each shape record
              for (const shape of shapeLinks) {
                await strapi.db.query('api::region-shape.region-shape').delete({
                  where: { id: shape.id }
                });
                shapesDeletedCount++;
              }
            } catch (err) {
              console.error(`[Country] Error deleting shapes for Region ${region.id}:`, err);
            }
          }
          console.log(`[Country] Deleted ${shapesDeletedCount} Region shapes`);
          
          // Then bulk delete Regions (parent records)
          await strapi.db.query('api::region.region').deleteMany({
            where: { country: countryData.id }
          });
          
          console.log(`[Country] ✅ Deleted ${existingRegions.length} Regions with their shapes`);
          importResults.push(`🗑️ Deleted ${existingRegions.length} Regions`);
        } else {
          console.log('[Country] No Regions found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting Regions:', error);
        console.error('[Country] Error stack:', error?.stack);
        importResults.push(`❌ Region deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Delete Highways if file was removed OR if file is set to null and Highways exist
    const shouldDeleteHighways = filesRemoved.highways || (filesChanged.highways && !countryData.highways_geojson_file);
    if (shouldDeleteHighways) {
      console.log('[Country] Highways GeoJSON file removed or set to null - checking for existing Highways...');
      try {
        // First check how many Highways exist for this country
        const existingHighways = await strapi.db.query('api::highway.highway').findMany({
          where: { country: countryData.id }
        });
        
        if (existingHighways.length > 0) {
          console.log(`[Country] Found ${existingHighways.length} existing Highways - deleting them and their shapes...`);
          
          // Delete Highway shapes using link table
          let shapesDeletedCount = 0;
          for (const highway of existingHighways) {
            try {
              // Find shape IDs from link table
              const shapeLinks = await strapi.db.connection('highway_shapes_highway_lnk')
                .select('highway_shape_id')
                .where('highway_id', highway.id);
              
              const shapeIds = shapeLinks.map(link => link.highway_shape_id);
              
              if (shapeIds.length > 0) {
                // Delete shapes
                await strapi.db.connection('highway_shapes')
                  .whereIn('id', shapeIds)
                  .del();
                shapesDeletedCount += shapeIds.length;
                
                // Delete link table entries
                await strapi.db.connection('highway_shapes_highway_lnk')
                  .where('highway_id', highway.id)
                  .del();
              }
            } catch (err) {
              console.error(`[Country] Error deleting shapes for Highway ${highway.id}:`, err);
            }
          }
          console.log(`[Country] Deleted ${shapesDeletedCount} Highway shapes`);
          
          // Then bulk delete Highways (parent records)
          await strapi.db.query('api::highway.highway').deleteMany({
            where: { country: countryData.id }
          });
          
          console.log(`[Country] ✅ Deleted ${existingHighways.length} Highways with their shapes`);
          importResults.push(`🗑️ Deleted ${existingHighways.length} Highways`);
        } else {
          console.log('[Country] No Highways found for this country - nothing to delete');
        }
      } catch (error: any) {
        console.error('[Country] Error deleting Highways:', error);
        console.error('[Country] Error stack:', error?.stack);
        importResults.push(`❌ Highway deletion failed: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Process POIs
    if (filesChanged.pois && countryData.pois_geojson_file) {
      console.log('[Country] ===== PROCESSING POIs =====');
      console.log('[Country] filesChanged.pois:', filesChanged.pois);
      console.log('[Country] countryData.pois_geojson_file:', countryData.pois_geojson_file);
      console.log('[Country] Processing POIs GeoJSON file...');
      try {
        await processPOIsGeoJSON(countryData);
        importResults.push('✅ POIs');
      } catch (error: any) {
        console.error('[Country] Error processing POIs:', error);
        importResults.push(`❌ POIs: ${error?.message || 'Unknown error'}`);
      }
    } else {
      console.log('[Country] SKIPPING POI processing - filesChanged.pois:', filesChanged.pois, ', has file:', !!countryData.pois_geojson_file);
    }
    
    // Process Landuse (only if file actually changed)
    if (filesChanged.landuse && countryData.landuse_geojson_file) {
      console.log('[Country] ===== PROCESSING LANDUSE =====');
      console.log('[Country] filesChanged.landuse:', filesChanged.landuse);
      console.log('[Country] countryData.landuse_geojson_file:', countryData.landuse_geojson_file);
      console.log('[Country] Processing Landuse GeoJSON file...');
      try {
        await processLanduseGeoJSON(countryData);
        importResults.push('✅ Landuse');
      } catch (error: any) {
        console.error('[Country] Error processing Landuse:', error);
        importResults.push(`❌ Landuse: ${error?.message || 'Unknown error'}`);
      }
    } else {
      console.log('[Country] SKIPPING Landuse processing - filesChanged.landuse:', filesChanged.landuse, ', has file:', !!countryData.landuse_geojson_file);
    }
    
    // Process Regions
    if (filesChanged.regions && countryData.regions_geojson_file) {
      console.log('[Country] Processing Regions GeoJSON file...');
      try {
        await processRegionsGeoJSON(countryData);
        importResults.push('✅ Regions');
      } catch (error: any) {
        console.error('[Country] Error processing Regions:', error);
        importResults.push(`❌ Regions: ${error?.message || 'Unknown error'}`);
      }
    }
    
    // Process Highways (only if file changed - consistent with POI/Landuse behavior)
    if (filesChanged.highways && countryData.highways_geojson_file) {
      console.log('[Country] ===== PROCESSING HIGHWAYS =====');
      console.log('[Country] filesChanged.highways:', filesChanged.highways);
      console.log('[Country] countryData.highways_geojson_file:', countryData.highways_geojson_file);
      console.log('[Country] Processing Highways GeoJSON file...');
      try {
        await processHighwaysGeoJSON(countryData);
        importResults.push('✅ Highways');
      } catch (error: any) {
        console.error('[Country] Error processing Highways:', error);
        importResults.push(`❌ Highways: ${error?.message || 'Unknown error'}`);
      }
    } else {
      console.log('[Country] SKIPPING Highways processing - filesChanged.highways:', filesChanged.highways, ', has file:', !!countryData.highways_geojson_file);
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
      
      console.log('[Country] ===== AFTER UPDATE COMPLETED =====');
    } catch (error: any) {
      console.error('[Country] ❌ FATAL ERROR in afterUpdate:', error);
      console.error('[Country] Error stack:', error?.stack);
      throw error; // Re-throw to let Strapi handle it
    }
  }
};
