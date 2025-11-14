/**
 * Custom Admin Component: GeoJSON Import Button
 * Displays a file picker that reads local GeoJSON files and imports them
 */

import React, { useState } from 'react';
import './import-geojson-button.css';

interface GeoJSONImportButtonProps {
  countryId: string;
  type: 'pois' | 'landuse' | 'regions' | 'highways';
  label: string;
}

export const GeoJSONImportButton: React.FC<GeoJSONImportButtonProps> = ({ 
  countryId, 
  type, 
  label 
}) => {
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setMessage('');

    try {
      // Read file content
      const fileContent = await file.text();
      const geojsonData = JSON.parse(fileContent);

      // Send to import endpoint
      const response = await fetch(`/api/countries/${countryId}/import-geojson-direct`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ type, geojsonData }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error?.message || 'Import failed');
      }

      const result = await response.json();
      setMessage(`✅ Imported ${result.data.featureCount || 0} features successfully!`);
      
      // Refresh page after 2 seconds
      setTimeout(() => window.location.reload(), 2000);
      
    } catch (error: any) {
      setMessage(`❌ Import failed: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="geojson-import-button">
      <div className="geojson-import-button__label">
        {label}
      </div>
      
      <label 
        htmlFor={`import-${type}`} 
        className={`geojson-import-button__file-label ${isLoading ? 'geojson-import-button__file-label--disabled' : ''}`}
      >
        <input
          id={`import-${type}`}
          type="file"
          accept=".json,.geojson"
          onChange={handleFileSelect}
          hidden
          disabled={isLoading}
        />
        <button
          type="button"
          onClick={() => document.getElementById(`import-${type}`)?.click()}
          disabled={isLoading}
          className="geojson-import-button__button"
        >
          {isLoading ? '⏳ Importing...' : '📁 Select GeoJSON File'}
        </button>
      </label>

      {message && (
        <div className={`geojson-import-button__message ${message.startsWith('✅') ? 'geojson-import-button__message--success' : 'geojson-import-button__message--error'}`}>
          {message}
        </div>
      )}
    </div>
  );
};

