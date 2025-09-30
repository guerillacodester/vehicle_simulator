import { v4 as uuidv4 } from 'uuid';

export default {
  async afterCreate(event: any) {
    const { result } = event;
    
    if (result.geojson_data) {
      await processGeoJSONData(result, result.short_name);
    }
  },

  async beforeUpdate(event: any) {
    const { data } = event.params;
    const routeId = event.params.where.id;
    
    // Only process shapes if geojson_data field is being updated
    if (!data.hasOwnProperty('geojson_data')) {
      console.log('beforeUpdate - geojson_data not being modified, skipping shape processing');
      return;
    }
    
    console.log('beforeUpdate - geojson_data is being modified');
    
    // Fix empty JSON field issue - convert empty string to null
    if (data.geojson_data === '' || data.geojson_data === undefined) {
      data.geojson_data = null;
    }
    
    // Get the current route to access short_name
    const currentRoute = await strapi.entityService.findOne('api::route.route', routeId);
    const routeIdentifier = data.short_name || currentRoute?.short_name;
    
    console.log('beforeUpdate - data keys:', Object.keys(data));
    console.log('beforeUpdate - geojson_data value:', data.geojson_data);
    console.log('beforeUpdate - using route identifier:', routeIdentifier);
    
    // Clear existing shapes before processing new data
    if (routeIdentifier) {
      await clearExistingShapes(routeIdentifier);
    }
    
    // Check if geojson_data has content to process
    if (data.geojson_data && data.geojson_data !== null) {
      console.log('Processing new GeoJSON data...');
      await processGeoJSONData(data, routeIdentifier);
    } else {
      console.log('No GeoJSON data to process (cleared or empty)');
    }
  },

  async beforeDelete(event: any) {
    const routeId = event.params.where.id;
    
    // Get the route to access short_name
    const route = await strapi.entityService.findOne('api::route.route', routeId);
    const routeIdentifier = route?.short_name;
    
    console.log('Route being deleted, cleaning up all associated shapes...');
    if (routeIdentifier) {
      await clearExistingShapes(routeIdentifier);
    }
  }
};

async function processGeoJSONData(routeData: any, routeId: string) {
  try {
    console.log('Processing GeoJSON data for route:', routeId);
    
    let geojson = routeData.geojson_data;
    
    if (typeof geojson === 'string') {
      geojson = JSON.parse(geojson);
    }
    
    if (!geojson || !geojson.features) {
      console.log('No valid GeoJSON features found');
      return;
    }
    
    console.log('Found', geojson.features.length, 'features in GeoJSON');

    for (let featureIndex = 0; featureIndex < geojson.features.length; featureIndex++) {
      const feature = geojson.features[featureIndex];
      
      if (feature.geometry && feature.geometry.type === 'LineString') {
        const coordinates = feature.geometry.coordinates;
        const shapeId = uuidv4();
        
        console.log('Creating shape', featureIndex + 1, ':', shapeId, 'with', coordinates.length, 'points');

        await strapi.entityService.create('api::route-shape.route-shape', {
          data: {
            route_shape_id: routeId + '_' + shapeId,
            route_id: routeId,
            shape_id: shapeId,
            variant_code: feature.properties?.variant_code || null,
            is_default: featureIndex === 0,
            publishedAt: new Date()
          }
        });

        for (let i = 0; i < coordinates.length; i++) {
          const [lon, lat] = coordinates[i];
          
          await strapi.entityService.create('api::shape.shape', {
            data: {
              shape_id: shapeId,
              shape_pt_lat: lat,
              shape_pt_lon: lon,
              shape_pt_sequence: i + 1,
              shape_dist_traveled: feature.properties?.shape_dist_traveled || null,
              is_active: true,
              publishedAt: new Date()
            }
          });
        }
        
        console.log('Created', coordinates.length, 'shape points for shape', shapeId);
      }
    }
    
    console.log('GeoJSON processing complete!');
    
  } catch (error) {
    console.error('Error processing GeoJSON:', error);
    throw error;
  }
}

async function clearExistingShapes(routeId: string) {
  try {
    console.log('Clearing existing shapes for route:', routeId);
    
    // Get all route-shapes for this route
    const routeShapes = await strapi.entityService.findMany('api::route-shape.route-shape', {
      filters: { route_id: String(routeId) }
    });

    console.log('Found', routeShapes.length, 'route-shapes to clean up');

    let totalShapePointsDeleted = 0;

    // Delete all associated shape points
    for (const routeShape of routeShapes) {
      if (routeShape.shape_id) {
        console.log('Cleaning shape_id:', routeShape.shape_id);
        
        const shapePoints = await strapi.entityService.findMany('api::shape.shape', {
          filters: { shape_id: routeShape.shape_id }
        });
        
        console.log('Found', shapePoints.length, 'shape points for shape_id:', routeShape.shape_id);
        
        for (const shapePoint of shapePoints) {
          await strapi.entityService.delete('api::shape.shape', shapePoint.id);
          totalShapePointsDeleted++;
        }
      }
    }

    // Delete route-shape relationships
    for (const routeShape of routeShapes) {
      console.log('Deleting route-shape:', routeShape.id);
      await strapi.entityService.delete('api::route-shape.route-shape', routeShape.id);
    }
    
    console.log('Cleanup complete: Deleted', totalShapePointsDeleted, 'shape points and', routeShapes.length, 'route-shapes');
    
  } catch (error) {
    console.error('Error clearing existing shapes:', error);
  }
}
