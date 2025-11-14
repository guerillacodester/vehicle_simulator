import React, { useState, useEffect } from 'react';
import { GeoJSONImportButton } from '../extensions/import-geojson-button';
import '../extensions/content-manager/country-importers.css';

const GeoJSONImportPage = () => {
  const [countries, setCountries] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCountry, setSelectedCountry] = useState<string | null>(null);

  useEffect(() => {
    fetchCountries();
  }, []);

  const fetchCountries = async () => {
    try {
      const response = await fetch('/api/countries');
      const data = await response.json();
      setCountries(data.data || []);
      if (data.data && data.data.length > 0) {
        setSelectedCountry(data.data[0].documentId);
      }
    } catch (error) {
      console.error('Failed to fetch countries:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="geojson-import-page">Loading...</div>;
  }

  return (
    <div className="geojson-import-page">
      <div className="geojson-import-page__header">
        <h1>GeoJSON Data Import</h1>
        <p>Import GeoJSON files directly from your computer into the database</p>
      </div>

      <div className="geojson-import-page__selector">
        <label htmlFor="country-select">
          <strong>Select Country:</strong>
        </label>
        <select
          id="country-select"
          value={selectedCountry || ''}
          onChange={(e) => setSelectedCountry(e.target.value)}
          className="geojson-import-page__select"
        >
          {countries.map((country) => (
            <option key={country.documentId} value={country.documentId}>
              {country.name}
            </option>
          ))}
        </select>
      </div>

      {selectedCountry && (
        <div className="geojson-import-panel">
          <h3 className="geojson-import-panel__title">
            Import GeoJSON Files
          </h3>
          <div className="geojson-importers-grid">
            <GeoJSONImportButton
              countryId={selectedCountry}
              type="pois"
              label="Import POIs/Amenities"
            />
            <GeoJSONImportButton
              countryId={selectedCountry}
              type="landuse"
              label="Import Landuse Zones"
            />
            <GeoJSONImportButton
              countryId={selectedCountry}
              type="regions"
              label="Import Regions"
            />
            <GeoJSONImportButton
              countryId={selectedCountry}
              type="highways"
              label="Import Highways"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default GeoJSONImportPage;
