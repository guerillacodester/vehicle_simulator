import React from 'react';
import { GeoJSONImportButton } from '../import-geojson-button';
import './country-importers.css';

// This creates a standalone panel with import buttons
const GeoJSONImportPanel = ({ data }: any) => {
  if (!data?.documentId) return null;

  return (
    <div className="geojson-import-panel">
      <h3 className="geojson-import-panel__title">
        GeoJSON Data Import
      </h3>
      <div className="geojson-importers-grid">
        <GeoJSONImportButton
          countryId={data.documentId}
          type="pois"
          label="Import POIs/Amenities"
        />
        <GeoJSONImportButton
          countryId={data.documentId}
          type="landuse"
          label="Import Landuse Zones"
        />
        <GeoJSONImportButton
          countryId={data.documentId}
          type="regions"
          label="Import Regions"
        />
        <GeoJSONImportButton
          countryId={data.documentId}
          type="highways"
          label="Import Highways"
        />
      </div>
    </div>
  );
};

export default GeoJSONImportPanel;
