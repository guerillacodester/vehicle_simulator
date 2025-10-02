import fs from 'fs';
import path from 'path';

export default {
  /**
   * Cascade delete: Remove all related geographic data when country is deleted
   */
  async beforeDelete(event: any) {
    const countryId = event.params.where.id;
    
    console.log(`[Country] Deleting country ${countryId} - cleaning up all related data...`);
    
    try {
      // Delete POIs
      const pois = await strapi.entityService.findMany('api::poi.poi', {
        filters: { country: countryId }
      });
      console.log(`[Country] Deleting ${pois.length} POIs...`);
      for (const poi of pois) {
        await strapi.entityService.delete('api::poi.poi', poi.id);
      }
      
      // Delete Places
      const places = await strapi.entityService.findMany('api::place.place', {
        filters: { country: countryId }
      });
      console.log(`[Country] Deleting ${places.length} Places...`);
      for (const place of places) {
        await strapi.entityService.delete('api::place.place', place.id);
      }
      
      // Delete Landuse Zones
      const zones = await strapi.entityService.findMany('api::landuse-zone.landuse-zone', {
        filters: { country: countryId }
      });
      console.log(`[Country] Deleting ${zones.length} Landuse Zones...`);
      for (const zone of zones) {
        await strapi.entityService.delete('api::landuse-zone.landuse-zone', zone.id);
      }
      
      // Delete Regions
      const regions = await strapi.entityService.findMany('api::region.region', {
        filters: { country: countryId }
      });
      console.log(`[Country] Deleting ${regions.length} Regions...`);
      for (const region of regions) {
        await strapi.entityService.delete('api::region.region', region.id);
      }
      
      console.log(`[Country] ✅ Cascade delete complete`);
      
    } catch (error) {
      console.error('[Country] Error during cascade delete:', error);
    }
  },

  /**
   * Track which GeoJSON files have changed
   */
  async beforeUpdate(event: any) {
    const { data } = event.params;
    
    // Track which GeoJSON files are being updated
    event.state = event.state || {};
    event.state.filesChanged = {
      pois: data.hasOwnProperty('pois_geojson_file'),
      places: data.hasOwnProperty('place_names_geojson_file'),
      landuse: data.hasOwnProperty('landuse_geojson_file'),
      regions: data.hasOwnProperty('regions_geojson_file')
    };
    
    console.log('[Country] File changes detected:', event.state.filesChanged);
  },

  /**
   * Process all uploaded GeoJSON files
   */
  async afterUpdate(event: any) {
    const { result } = event;
    const filesChanged = event.state?.filesChanged || {};
    
    const importResults = [];
    
    // Process POIs
    if (filesChanged.pois && result.pois_geojson_file) {
      console.log('[Country] Processing POIs GeoJSON file...');
      try {
        await processPOIsGeoJSON(result);
        importResults.push('✅ POIs');
      } catch (error) {
        console.error('[Country] Error processing POIs:', error);
        importResults.push(`❌ POIs: ${error.message}`);
      }
    }
    
    // Process Places
    if (filesChanged.places && result.place_names_geojson_file) {
      console.log('[Country] Processing Places GeoJSON file...');
      try {
        await processPlacesGeoJSON(result);
        importResults.push('✅ Places');
      } catch (error) {
        console.error('[Country] Error processing Places:', error);
        importResults.push(`❌ Places: ${error.message}`);
      }
    }
    
    // Process Landuse
    if (filesChanged.landuse && result.landuse_geojson_file) {
      console.log('[Country] Processing Landuse GeoJSON file...');
      try {
        await processLanduseGeoJSON(result);
        importResults.push('✅ Landuse');
      } catch (error) {
        console.error('[Country] Error processing Landuse:', error);
        importResults.push(`❌ Landuse: ${error.message}`);
      }
    }
    
    // Process Regions
    if (filesChanged.regions && result.regions_geojson_file) {
      console.log('[Country] Processing Regions GeoJSON file...');
      try {
        await processRegionsGeoJSON(result);
        importResults.push('✅ Regions');
      } catch (error) {
        console.error('[Country] Error processing Regions:', error);
        importResults.push(`❌ Regions: ${error.message}`);
      }
    }
    
    // Update import status if any files were processed
    if (importResults.length > 0) {
      await strapi.entityService.update('api::country.country', result.id, {
        data: {
          geodata_import_status: `${importResults.join(', ')} at ${new Date().toISOString()}`,
          geodata_last_import: new Date()
        }
      });
    }
  }
};

/**
 * Process POIs GeoJSON file and import to database
 */
async function processPOIsGeoJSON(country: any) {
  const file = country.pois_geojson_file;
  
  if (!file) {
    console.log('[Country] No POIs GeoJSON file to process');
    return;
  }
  
  // Read file from uploads directory
  const filePath = path.join(strapi.dirs.static.public, file.url);
  
  if (!fs.existsSync(filePath)) {
    throw new Error(`POIs GeoJSON file not found: ${filePath}`);
  }
  
  const fileContent = fs.readFileSync(filePath, 'utf-8');
  const geojson = JSON.parse(fileContent);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: No features array found');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} POI features...`);
  
  // Clear existing POIs for this country
  const existingPOIs = await strapi.entityService.findMany('api::poi.poi', {
    filters: { country: country.id }
  });
  
  console.log(`[Country] Deleting ${existingPOIs.length} existing POIs...`);
  
  for (const poi of existingPOIs) {
    await strapi.entityService.delete('api::poi.poi', poi.id);
  }
  
  // Import POIs in chunks (to avoid timeout)
  const CHUNK_SIZE = 100;
  let importedCount = 0;
  
  for (let i = 0; i < geojson.features.length; i += CHUNK_SIZE) {
    const chunk = geojson.features.slice(i, i + CHUNK_SIZE);
    const poisToCreate = [];
    
    for (const feature of chunk) {
      // Only process Point features
      if (feature.geometry?.type !== 'Point') {
        continue;
      }
      
      const [lon, lat] = feature.geometry.coordinates;
      const props = feature.properties || {};
      
      // Validate coordinates
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        console.warn(`[Country] Invalid coordinates: [${lon}, ${lat}]`);
        continue;
      }
      
      // Map OSM amenity to POI type
      const poiType = mapAmenityType(props.amenity);
      
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
    
    // Bulk create chunk
    if (poisToCreate.length > 0) {
      await strapi.db.query('api::poi.poi').createMany({
        data: poisToCreate
      });
      
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
  const mapping = {
    'bus_station': 'bus_station',
    'bus_stop': 'bus_station',
    'marketplace': 'marketplace',
    'market': 'marketplace',
    'hospital': 'hospital',
    'clinic': 'clinic',
    'doctors': 'clinic',
    'school': 'school',
    'college': 'university',
    'university': 'university',
    'police': 'police_station',
    'fire_station': 'fire_station',
    'place_of_worship': 'place_of_worship',
    'church': 'place_of_worship',
    'mosque': 'place_of_worship',
    'temple': 'place_of_worship',
    'bank': 'bank',
    'post_office': 'post_office',
    'restaurant': 'restaurant',
    'cafe': 'cafe',
    'pharmacy': 'pharmacy',
    'fuel': 'fuel_station',
    'parking': 'parking',
    'library': 'library',
    'community_centre': 'community_center'
  };
  
  return mapping[amenity?.toLowerCase()] || 'other';
}

/**
 * Process Places GeoJSON file and import to database
 */
async function processPlacesGeoJSON(country: any) {
  const file = country.place_names_geojson_file;
  
  if (!file?.url) {
    console.warn('[Country] No Places GeoJSON file URL found');
    return 0;
  }
  
  console.log(`[Country] Reading Places GeoJSON from: ${file.url}`);
  
  // Read and parse GeoJSON
  const filePath = path.join(strapi.dirs.static.public, file.url);
  const content = await fs.readFile(filePath, 'utf-8');
  const geojson = JSON.parse(content);
  
  if (!geojson.features || !Array.isArray(geojson.features)) {
    throw new Error('Invalid GeoJSON: missing features array');
  }
  
  console.log(`[Country] Processing ${geojson.features.length} place name features...`);
  
  // Delete existing places for this country
  await strapi.db.query('api::place.place').deleteMany({
    where: { country: country.id }
  });
  
  let importedCount = 0;
  const chunkSize = 100;
  
  // Process in chunks
  for (let i = 0; i < geojson.features.length; i += chunkSize) {
    const chunk = geojson.features.slice(i, i + chunkSize);
    const placesToCreate = [];
    
    for (const feature of chunk) {
      const props = feature.properties || {};
      const coords = feature.geometry?.coordinates;
      
      if (!coords || coords.length < 2) continue;
      
      const [lon, lat] = coords;
      
      // Validate coordinates
      if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
        console.warn(`[Country] Invalid coordinates: [${lon}, ${lat}]`);
        continue;
      }
      
      // Map OSM place type
      const placeType = mapPlaceType(props.place || props.type);
      
      placesToCreate.push({
        name: props.name || 'Unnamed Place',
        place_type: placeType,
        latitude: lat,
        longitude: lon,
        population: props.population ? parseInt(props.population) : null,
        importance: props.importance || 0,
        osm_id: props.osm_id || props.id,
        tags: props.tags ? JSON.stringify(props.tags) : null,
        country: country.id,
        publishedAt: new Date()
      });
    }
    
    // Bulk create chunk
    if (placesToCreate.length > 0) {
      await strapi.db.query('api::place.place').createMany({
        data: placesToCreate
      });
      
      importedCount += placesToCreate.length;
      console.log(`[Country] Places import progress: ${importedCount}/${geojson.features.length}`);
    }
  }
  
  console.log(`[Country] ✅ Successfully imported ${importedCount} Places`);
  
  return importedCount;
}

/**
 * Helper: Map OSM place type to Place type
 */
function mapPlaceType(placeType: string): string {
  const mapping = {
    'city': 'city',
    'town': 'town',
    'village': 'village',
    'hamlet': 'hamlet',
    'suburb': 'suburb',
    'neighbourhood': 'neighbourhood',
    'neighborhood': 'neighbourhood',
    'quarter': 'neighbourhood',
    'isolated_dwelling': 'hamlet'
  };
  
  return mapping[placeType?.toLowerCase()] || 'other';
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
        lat = ring.reduce((sum, p) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum, p) => sum + p[0], 0) / ring.length;
      } else if (feature.geometry.type === 'MultiPolygon' && coords[0]?.[0]?.length > 0) {
        // Use first polygon's outer ring
        const ring = coords[0][0];
        lat = ring.reduce((sum, p) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum, p) => sum + p[0], 0) / ring.length;
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
        center_lat: lat,
        center_lon: lon,
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
    
    // Bulk create chunk
    if (zonesToCreate.length > 0) {
      await strapi.db.query('api::landuse-zone.landuse-zone').createMany({
        data: zonesToCreate
      });
      
      importedCount += zonesToCreate.length;
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
  const mapping = {
    'residential': 'residential',
    'commercial': 'commercial',
    'industrial': 'industrial',
    'retail': 'commercial',
    'education': 'education',
    'institutional': 'institutional',
    'recreation_ground': 'recreation',
    'park': 'recreation',
    'grass': 'green_space',
    'forest': 'green_space',
    'farmland': 'agricultural',
    'construction': 'mixed_use',
    'brownfield': 'mixed_use'
  };
  
  return mapping[landuse?.toLowerCase()] || 'mixed_use';
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
        lat = ring.reduce((sum, p) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum, p) => sum + p[0], 0) / ring.length;
      } else if (feature.geometry.type === 'MultiPolygon' && coords[0]?.[0]?.length > 0) {
        const ring = coords[0][0];
        lat = ring.reduce((sum, p) => sum + p[1], 0) / ring.length;
        lon = ring.reduce((sum, p) => sum + p[0], 0) / ring.length;
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
