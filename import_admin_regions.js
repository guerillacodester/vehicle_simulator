/**
 * Import Admin Level Regions from GeoJSON files
 * This script imports regions from the 4 admin level GeoJSON files into the regions table
 */

const fs = require('fs');
const path = require('path');
const { Client } = require('pg');

// Database configuration
const dbConfig = {
  user: 'david',
  host: '127.0.0.1',
  database: 'arknettransit',
  password: 'Ga25w123!',
  port: 5432,
};

// Admin level files to import
const adminFiles = [
  { file: 'admin_level_6_polygon.geojson', level: 6, name: 'Parish' },
  { file: 'admin_level_8_polygon.geojson', level: 8, name: 'Town' },
  { file: 'admin_level_9_polygon.geojson', level: 9, name: 'Suburb' },
  { file: 'admin_level_10_polygon.geojson', level: 10, name: 'Neighbourhood' },
];

// Convert GeoJSON geometry to WKT
function geometryToWKT(geometry) {
  if (geometry.type === 'MultiPolygon') {
    const polygons = geometry.coordinates.map(polygon => {
      const rings = polygon.map(ring => {
        const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
        return `(${coords})`;
      }).join(', ');
      return `(${rings})`;
    }).join(', ');
    return `MULTIPOLYGON(${polygons})`;
  } else if (geometry.type === 'Polygon') {
    const rings = geometry.coordinates.map(ring => {
      const coords = ring.map(coord => `${coord[0]} ${coord[1]}`).join(', ');
      return `(${coords})`;
    }).join(', ');
    return `POLYGON(${rings})`;
  }
  throw new Error(`Unsupported geometry type: ${geometry.type}`);
}

async function importAdminRegions() {
  const client = new Client(dbConfig);
  
  try {
    await client.connect();
    console.log('Connected to database');

    // Get country ID for Barbados
    const countryResult = await client.query(
      "SELECT id FROM countries WHERE name = 'Barbados' LIMIT 1"
    );
    
    if (countryResult.rows.length === 0) {
      throw new Error('Barbados country not found in database');
    }
    
    const countryId = countryResult.rows[0].id;
    console.log(`Country ID for Barbados: ${countryId}`);

    let totalImported = 0;

    for (const adminFile of adminFiles) {
      console.log(`\n=== Processing ${adminFile.file} (Level ${adminFile.level}: ${adminFile.name}) ===`);
      
      const filePath = path.join(__dirname, 'sample_data', adminFile.file);
      if (!fs.existsSync(filePath)) {
        console.error(`File not found: ${filePath}`);
        continue;
      }

      // Get admin_level ID
      const adminLevelResult = await client.query(
        'SELECT id FROM admin_levels WHERE level = $1',
        [adminFile.level]
      );
      
      if (adminLevelResult.rows.length === 0) {
        console.error(`Admin level ${adminFile.level} not found in database`);
        continue;
      }
      
      const adminLevelId = adminLevelResult.rows[0].id;
      console.log(`Admin Level ID: ${adminLevelId}`);

      // Read GeoJSON file
      const geojsonContent = fs.readFileSync(filePath, 'utf8');
      const geojson = JSON.parse(geojsonContent);
      const features = geojson.features;
      
      console.log(`Found ${features.length} features`);

      let imported = 0;
      let skipped = 0;

      for (const feature of features) {
        const properties = feature.properties;
        const geometry = feature.geometry;

        const name = properties.name || 'Unnamed';
        const osmId = properties.osm_id || properties['osm:id'] || null;
        const fullId = properties.full_id || properties['full:id'] || null;

        try {
          // Convert geometry to WKT
          const wkt = geometryToWKT(geometry);

          // Insert region
          const { randomUUID } = require('crypto');
          const documentId = randomUUID();
          const timestamp = new Date().toISOString();

          await client.query(`
            INSERT INTO regions (
              document_id, name, osm_id, full_id, admin_level_id,
              geom, created_at, updated_at, published_at
            ) VALUES (
              $1, $2, $3, $4, $5,
              ST_GeomFromText($6, 4326), $7, $8, $9
            )
          `, [
            documentId, name, osmId, fullId, adminLevelId,
            wkt, timestamp, timestamp, timestamp
          ]);

          // Create junction table entry
          const regionResult = await client.query(
            'SELECT id FROM regions WHERE document_id = $1',
            [documentId]
          );
          
          if (regionResult.rows.length > 0) {
            const regionId = regionResult.rows[0].id;
            await client.query(`
              INSERT INTO regions_admin_level_lnk (region_id, admin_level_id)
              VALUES ($1, $2)
              ON CONFLICT DO NOTHING
            `, [regionId, adminLevelId]);
          }

          // Also link to country (if countries_regions_lnk table exists)
          try {
            if (regionResult.rows.length > 0) {
              const regionId = regionResult.rows[0].id;
              await client.query(`
                INSERT INTO countries_regions_lnk (country_id, region_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
              `, [countryId, regionId]);
            }
          } catch (err) {
            // Table might not exist, skip silently
          }

          imported++;
        } catch (error) {
          console.error(`Error importing feature "${name}":`, error.message);
          skipped++;
        }
      }

      console.log(`Imported: ${imported}, Skipped: ${skipped}`);
      totalImported += imported;
    }

    console.log(`\n=== Import Complete ===`);
    console.log(`Total regions imported: ${totalImported}`);

    // Verify the import
    const stats = await client.query(`
      SELECT al.level, al.name, COUNT(r.id) as region_count
      FROM admin_levels al
      LEFT JOIN regions r ON r.admin_level_id = al.id
      GROUP BY al.level, al.name
      ORDER BY al.level
    `);

    console.log('\n=== Import Summary by Admin Level ===');
    stats.rows.forEach(row => {
      console.log(`Level ${row.level} (${row.name}): ${row.region_count} regions`);
    });

  } catch (error) {
    console.error('Error during import:', error);
    throw error;
  } finally {
    await client.end();
    console.log('\nDatabase connection closed');
  }
}

// Run the import
importAdminRegions().catch(err => {
  console.error('Fatal error:', err);
  process.exit(1);
});
