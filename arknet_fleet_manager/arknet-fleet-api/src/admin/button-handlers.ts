/**
 * GeoJSON Import Button Handlers
 * 
 * This file contains button handler functions for the Country content type's
 * GeoJSON import action buttons. These handlers run in the browser (admin panel)
 * and communicate with the backend via Socket.IO for real-time progress updates.
 * 
 * Architecture:
 * 1. User clicks button in admin panel
 * 2. Handler shows confirmation dialog
 * 3. Handler calls backend API endpoint
 * 4. Backend starts import job and returns jobId
 * 5. Handler connects to Socket.IO for progress updates
 * 6. Backend emits progress events during import
 * 7. Handler updates field metadata with progress
 * 8. User sees real-time progress in UI
 */

import { io, Socket } from 'socket.io-client';

// ============================================================================
// TypeScript Declarations
// ============================================================================

declare global {
  interface Window {
    handleImportHighway: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => Promise<void>;
    handleImportAmenity: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => Promise<void>;
    handleImportLanduse: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => Promise<void>;
    handleImportBuilding: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => Promise<void>;
    handleImportAdmin: (fieldName: string, fieldValue: any, onChange?: (value: any) => void) => Promise<void>;
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Extract country ID from current URL
 * URL format: /admin/content-manager/collection-types/api::country.country/{id}
 */
function getCountryId(): string | null {
  const pathParts = window.location.pathname.split('/');
  const countryId = pathParts[pathParts.length - 1];
  
  if (!countryId || countryId === 'create') {
    return null;
  }
  
  return countryId;
}

/**
 * Get JWT authentication token from localStorage
 */
function getAuthToken(): string | null {
  return localStorage.getItem('jwtToken');
}

/**
 * Get Strapi API base URL
 */
function getApiBaseUrl(): string {
  // In development, Strapi runs on localhost:1337
  // In production, this would be configured differently
  return window.location.origin;
}

// ============================================================================
// Core Import Handler (Generic)
// ============================================================================

/**
 * Generic import handler for any GeoJSON file type
 * 
 * @param fileType - The GeoJSON file type (highway, amenity, landuse, building, admin)
 * @param fieldName - The schema field name
 * @param fieldValue - Current field value (previous import metadata)
 * @param onChange - Callback to update field metadata
 */
async function handleGeoJSONImport(
  fileType: string,
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> {
  console.log(`[${fileType}] Import button clicked`, { fieldName, fieldValue });

  // Step 1: Get country ID
  const countryId = getCountryId();
  if (!countryId) {
    alert('❌ Error: Cannot determine country ID from URL');
    return;
  }

  // Step 2: Show confirmation dialog
  const confirmed = confirm(
    `Import ${fileType}.geojson for this country?\n\n` +
    `This will:\n` +
    `- Parse the GeoJSON file\n` +
    `- Extract features and geometries\n` +
    `- Store data in database\n` +
    `- Update import status\n\n` +
    `${fileType === 'building' ? '⚠️ Note: building.geojson is 658MB and may take several minutes\n\n' : ''}` +
    `Continue?`
  );

  if (!confirmed) {
    console.log(`[${fileType}] Import cancelled by user`);
    return;
  }

  // Step 3: Get authentication
  const token = getAuthToken();
  if (!token) {
    alert('❌ Error: Not authenticated. Please log in again.');
    return;
  }

  // Step 4: Initialize metadata with "starting" status
  if (onChange) {
    onChange({
      status: 'starting',
      fileType: fileType,
      startedAt: new Date().toISOString(),
      progress: 0,
      featuresImported: 0,
      message: 'Initializing import...'
    });
  }

  try {
    // Step 5: Call backend API to start import
    const apiUrl = `${getApiBaseUrl()}/api/import-geojson/${fileType}`;
    console.log(`[${fileType}] Calling API:`, apiUrl);

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({
        countryId: countryId
      })
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API call failed: ${response.status} ${response.statusText}\n${errorText}`);
    }

    const result = await response.json();
    console.log(`[${fileType}] Import job started:`, result);

    const jobId = result.jobId || result.data?.jobId;
    if (!jobId) {
      throw new Error('No jobId returned from API');
    }

    // Step 6: Update metadata with job started
    if (onChange) {
      onChange({
        status: 'in_progress',
        fileType: fileType,
        startedAt: new Date().toISOString(),
        jobId: jobId,
        progress: 0,
        featuresImported: 0,
        message: 'Import job started, connecting for progress updates...'
      });
    }

    // Step 7: Connect to Socket.IO for real-time progress
    const socket: Socket = io(getApiBaseUrl(), {
      auth: {
        token: token
      },
      transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
      console.log(`[${fileType}] Socket.IO connected`, socket.id);
      
      if (onChange) {
        onChange({
          status: 'in_progress',
          fileType: fileType,
          startedAt: new Date().toISOString(),
          jobId: jobId,
          progress: 0,
          featuresImported: 0,
          message: 'Connected to progress stream...',
          socketId: socket.id
        });
      }
    });

    // Step 8: Listen for progress events
    socket.on(`import:progress:${jobId}`, (data: any) => {
      console.log(`[${fileType}] Progress update:`, data);
      
      if (onChange) {
        onChange({
          status: 'in_progress',
          fileType: fileType,
          startedAt: fieldValue?.startedAt || new Date().toISOString(),
          jobId: jobId,
          progress: data.progress || 0,
          featuresImported: data.featuresImported || 0,
          currentChunk: data.currentChunk,
          totalChunks: data.totalChunks,
          message: data.message || `Processing... ${data.progress}%`,
          lastUpdate: new Date().toISOString()
        });
      }
    });

    // Step 9: Listen for completion event
    socket.on(`import:complete:${jobId}`, (data: any) => {
      console.log(`[${fileType}] Import complete:`, data);
      
      socket.disconnect();
      
      if (onChange) {
        onChange({
          status: 'completed',
          fileType: fileType,
          startedAt: fieldValue?.startedAt || new Date().toISOString(),
          completedAt: new Date().toISOString(),
          jobId: jobId,
          progress: 100,
          featuresImported: data.totalFeatures || data.featuresImported || 0,
          duration: data.duration,
          message: 'Import completed successfully!'
        });
      }

      alert(
        `✅ Import Complete!\n\n` +
        `File: ${fileType}.geojson\n` +
        `Features imported: ${data.totalFeatures || 0}\n` +
        `Duration: ${data.duration || 'unknown'}s`
      );
    });

    // Step 10: Listen for error events
    socket.on(`import:error:${jobId}`, (error: any) => {
      console.error(`[${fileType}] Import error:`, error);
      
      socket.disconnect();
      
      if (onChange) {
        onChange({
          status: 'failed',
          fileType: fileType,
          startedAt: fieldValue?.startedAt || new Date().toISOString(),
          failedAt: new Date().toISOString(),
          jobId: jobId,
          error: error.message || 'Unknown error',
          message: `Import failed: ${error.message || 'Unknown error'}`
        });
      }

      alert(`❌ Import Failed!\n\n${error.message || 'Unknown error'}`);
    });

    // Step 11: Handle Socket.IO connection errors
    socket.on('connect_error', (error: Error) => {
      console.error(`[${fileType}] Socket.IO connection error:`, error);
      
      if (onChange) {
        onChange({
          status: 'failed',
          fileType: fileType,
          startedAt: fieldValue?.startedAt || new Date().toISOString(),
          failedAt: new Date().toISOString(),
          jobId: jobId,
          error: `Connection error: ${error.message}`,
          message: 'Failed to connect to progress stream'
        });
      }
    });

    socket.on('disconnect', (reason: string) => {
      console.log(`[${fileType}] Socket.IO disconnected:`, reason);
    });

  } catch (error) {
    console.error(`[${fileType}] Import handler error:`, error);
    
    if (onChange) {
      onChange({
        status: 'failed',
        fileType: fileType,
        startedAt: fieldValue?.startedAt || new Date().toISOString(),
        failedAt: new Date().toISOString(),
        error: (error as Error).message,
        message: `Import failed: ${(error as Error).message}`
      });
    }

    alert(`❌ Import Failed!\n\n${(error as Error).message}`);
  }
}

// ============================================================================
// Specific File Type Handlers
// ============================================================================

/**
 * Handler for Highway GeoJSON import
 * Button: 🛣️ Import Highways
 */
window.handleImportHighway = async (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> => {
  await handleGeoJSONImport('highway', fieldName, fieldValue, onChange);
};

/**
 * Handler for Amenity GeoJSON import
 * Button: 🏪 Import Amenities
 */
window.handleImportAmenity = async (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> => {
  await handleGeoJSONImport('amenity', fieldName, fieldValue, onChange);
};

/**
 * Handler for Landuse GeoJSON import
 * Button: 🌳 Import Land Use
 */
window.handleImportLanduse = async (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> => {
  await handleGeoJSONImport('landuse', fieldName, fieldValue, onChange);
};

/**
 * Handler for Building GeoJSON import
 * Button: 🏢 Import Buildings
 * Note: building.geojson is 658MB - this will take longer
 */
window.handleImportBuilding = async (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> => {
  await handleGeoJSONImport('building', fieldName, fieldValue, onChange);
};

/**
 * Handler for Admin Boundaries GeoJSON import
 * Button: 🗺️ Import Admin Boundaries
 */
window.handleImportAdmin = async (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> => {
  await handleGeoJSONImport('admin', fieldName, fieldValue, onChange);
};

// ============================================================================
// Export (for TypeScript module system)
// ============================================================================

export {};
