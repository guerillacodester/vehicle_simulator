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
 * Get JWT authentication token from Strapi admin session
 * Strapi admin uses a different auth mechanism than the public API
 */
function getAuthToken(): string | null {
  // Try sessionStorage first (Strapi v5 may use this)
  const tokenKeys = [
    'jwtToken',
    'strapi_jwt', 
    'token',
    'strapi-token',
  ];

  // Check sessionStorage
  for (const key of tokenKeys) {
    const token = sessionStorage.getItem(key);
    if (token) {
      console.log(`Found token in sessionStorage key: ${key}`);
      return token;
    }
  }

  // Check localStorage
  for (const key of tokenKeys) {
    const token = localStorage.getItem(key);
    if (token) {
      console.log(`Found token in localStorage key: ${key}`);
      return token;
    }
  }

  // Try to get admin token from various Strapi v5 structures
  try {
    // Method 1: strapi-admin-auth object
    const strapiAuth = sessionStorage.getItem('strapi-admin-auth') || localStorage.getItem('strapi-admin-auth');
    if (strapiAuth) {
      const authData = JSON.parse(strapiAuth);
      if (authData?.token) {
        console.log('Found token in strapi-admin-auth');
        return authData.token;
      }
    }
    
    // Method 2: Check for JWT pattern in all storage
    const allStorage = [
      { name: 'sessionStorage', storage: sessionStorage },
      { name: 'localStorage', storage: localStorage }
    ];
    
    for (const { name, storage } of allStorage) {
      for (let i = 0; i < storage.length; i++) {
        const key = storage.key(i);
        if (key) {
          const value = storage.getItem(key);
          if (value && value.startsWith('eyJ')) {
            console.log(`Found JWT-like token in ${name} key: ${key}`);
            return value;
          }
        }
      }
    }
  } catch (e) {
    console.error('Failed to parse auth data:', e);
  }

  console.warn('No authentication token found - will try cookie-based auth');
  return null;
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
  onChange?: (value: any) => void,
  additionalParams?: Record<string, any>
): Promise<void> {
  console.log(`[${fileType}] Import button clicked`, { fieldName, fieldValue, additionalParams });

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

  // Step 3: Get authentication token (optional - will fall back to cookies)
  const token = getAuthToken();
  
  // Step 4: Initialize metadata with "starting" status
  // Note: onChange disabled for now - causes Form.tsx errors
  // if (onChange) {
  //   try {
  //     onChange({
  //       status: 'starting',
  //       fileType: fileType,
  //       startedAt: new Date().toISOString(),
  //       progress: 0,
  //       featuresImported: 0,
  //       message: 'Initializing import...'
  //     });
  //   } catch (e) {
  //     console.warn('[Import] onChange failed (non-critical):', e);
  //   }
  // }

  try {
    // Step 5: Call backend API to start import
    const apiUrl = `${getApiBaseUrl()}/api/import-geojson/${fileType}`;
    console.log(`[${fileType}] Calling API:`, apiUrl);

    // Build headers - use token if available, otherwise rely on cookies
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
      console.log(`[${fileType}] Using Bearer token authentication`);
    } else {
      console.log(`[${fileType}] Using cookie-based authentication`);
    }

    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: headers,
      credentials: 'include', // Include cookies for Strapi admin auth
      body: JSON.stringify({
        countryId: countryId,
        ...additionalParams  // Include admin level or other parameters
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
    // TODO: Fix onChange to work with Strapi Form component
    // if (onChange) {
    //   onChange({
    //     status: 'in_progress',
    //     fileType: fileType,
    //     startedAt: new Date().toISOString(),
    //     jobId: jobId,
    //     progress: 0,
    //     featuresImported: 0,
    //     message: 'Import job started, connecting for progress updates...'
    //   });
    // }

    // Step 7: Connect to Socket.IO for real-time progress
    const socket: Socket = io(getApiBaseUrl(), {
      auth: {
        token: token
      },
      transports: ['websocket', 'polling']
    });

    socket.on('connect', () => {
      console.log(`[${fileType}] Socket.IO connected`, socket.id);
      
      // TODO: Fix onChange
      // if (onChange) {
      //   onChange({
      //     status: 'in_progress',
      //     fileType: fileType,
      //     startedAt: new Date().toISOString(),
      //     jobId: jobId,
      //     progress: 0,
      //     featuresImported: 0,
      //     message: 'Connected to progress stream...',
      //     socketId: socket.id
      //   });
      // }
    });

    // Step 8: Listen for progress events
    socket.on(`import:progress:${jobId}`, (data: any) => {
      console.log(`[${fileType}] Progress update:`, data);
      
      // TODO: Fix onChange
      // if (onChange) {
      //   onChange({
      //     status: 'in_progress',
      //     fileType: fileType,
      //     startedAt: fieldValue?.startedAt || new Date().toISOString(),
      //     jobId: jobId,
      //     progress: data.progress || 0,
      //     featuresImported: data.featuresImported || 0,
      //     currentChunk: data.currentChunk,
      //     totalChunks: data.totalChunks,
      //     message: data.message || `Processing... ${data.progress}%`,
      //     lastUpdate: new Date().toISOString()
      //   });
      // }
    });

    // Step 9: Listen for completion event
    socket.on(`import:complete:${jobId}`, (data: any) => {
      console.log(`[${fileType}] Import complete:`, data);
      
      socket.disconnect();
      
      // TODO: Fix onChange
      // if (onChange) {
      //   onChange({
      //     status: 'completed',
      //     fileType: fileType,
      //     startedAt: fieldValue?.startedAt || new Date().toISOString(),
      //     completedAt: new Date().toISOString(),
      //     jobId: jobId,
      //     progress: 100,
      //     featuresImported: data.totalFeatures || data.featuresImported || 0,
      //     duration: data.duration,
      //     message: 'Import completed successfully!'
      //   });
      // }

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
      
      // TODO: Fix onChange
      // if (onChange) {
      //   onChange({
      //     status: 'failed',
      //     fileType: fileType,
      //     startedAt: fieldValue?.startedAt || new Date().toISOString(),
      //     failedAt: new Date().toISOString(),
      //     jobId: jobId,
      //     error: error.message || 'Unknown error',
      //     message: `Import failed: ${error.message || 'Unknown error'}`
      //   });
      // }

      alert(`❌ Import Failed!\n\n${error.message || 'Unknown error'}`);
    });

    // Step 11: Handle Socket.IO connection errors
    socket.on('connect_error', (error: Error) => {
      console.error(`[${fileType}] Socket.IO connection error:`, error);
      
      // TODO: Fix onChange
      // if (onChange) {
      //   onChange({
      //     status: 'failed',
      //     fileType: fileType,
      //     startedAt: fieldValue?.startedAt || new Date().toISOString(),
      //     failedAt: new Date().toISOString(),
      //     jobId: jobId,
      //     error: `Connection error: ${error.message}`,
      //     message: 'Failed to connect to progress stream'
      //   });
      // }
    });

    socket.on('disconnect', (reason: string) => {
      console.log(`[${fileType}] Socket.IO disconnected:`, reason);
    });

  } catch (error) {
    console.error(`[${fileType}] Import handler error:`, error);
    
    // TODO: Fix onChange
    // if (onChange) {
    //   onChange({
    //     status: 'failed',
    //     fileType: fileType,
    //     startedAt: fieldValue?.startedAt || new Date().toISOString(),
    //     failedAt: new Date().toISOString(),
    //     error: (error as Error).message,
    //     message: `Import failed: ${(error as Error).message}`
    //   });
    // }

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
 * 
 * IMPORTANT: Requires admin level selection before import
 * User must choose: Parish (6), Town (8), Suburb (9), or Neighbourhood (10)
 */
window.handleImportAdmin = async (
  fieldName: string,
  fieldValue: any,
  onChange?: (value: any) => void
): Promise<void> => {
  const countryId = getCountryId();
  if (!countryId) {
    alert('⚠️ Please save the country first before importing admin boundaries.');
    return;
  }

  // Fetch available admin levels from API
  try {
    const apiBase = getApiBaseUrl();
    const token = getAuthToken();
    
    const response = await fetch(`${apiBase}/api/admin-levels`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      }
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch admin levels: ${response.statusText}`);
    }
    
    const data = await response.json();
    const adminLevels = data.data || [];
    
    if (adminLevels.length === 0) {
      alert('⚠️ No admin levels found in database. Please seed admin_levels table first.');
      return;
    }
    
    // Create a custom modal dialog with dropdown
    const sortedLevels = adminLevels.sort((a: any, b: any) => a.level - b.level);
    
    // Create modal overlay
    const modal = document.createElement('div');
    modal.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(0, 0, 0, 0.5);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 10000;
    `;
    
    // Create modal content
    const modalContent = document.createElement('div');
    modalContent.style.cssText = `
      background: #212134;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      max-width: 500px;
      width: 90%;
    `;
    
    modalContent.innerHTML = `
      <h2 style="margin: 0 0 20px 0; color: #ffffff; font-size: 24px; font-weight: 600;">
        🗺️ Select Admin Level
      </h2>
      <p style="margin: 0 0 20px 0; color: #a5a5ba; font-size: 14px;">
        Choose the administrative level for the regions you want to import:
      </p>
      <select id="adminLevelSelect" style="
        width: 100%;
        padding: 12px;
        font-size: 14px;
        border: 1px solid #32324d;
        border-radius: 4px;
        margin-bottom: 20px;
        cursor: pointer;
        background: #32324d;
        color: #ffffff;
      ">
        ${sortedLevels.map((level: any) => `
          <option value="${level.id}">
            ${level.name} (Admin Level ${level.level})${level.description ? ' - ' + level.description : ''}
          </option>
        `).join('')}
      </select>
      <div style="display: flex; gap: 10px; justify-content: flex-end;">
        <button id="cancelBtn" style="
          padding: 10px 20px;
          font-size: 14px;
          border: 1px solid #32324d;
          background: transparent;
          color: #ffffff;
          border-radius: 4px;
          cursor: pointer;
          transition: background 0.2s;
        " onmouseover="this.style.background='#32324d'" onmouseout="this.style.background='transparent'">Cancel</button>
        <button id="confirmBtn" style="
          padding: 10px 20px;
          font-size: 14px;
          border: none;
          background: #4945ff;
          color: white;
          border-radius: 4px;
          cursor: pointer;
          transition: background 0.2s;
        " onmouseover="this.style.background='#7b79ff'" onmouseout="this.style.background='#4945ff'">Import</button>
      </div>
    `;
    
    modal.appendChild(modalContent);
    document.body.appendChild(modal);
    
    // Wait for user selection
    const adminLevel = await new Promise<any>((resolve) => {
      const selectElement = document.getElementById('adminLevelSelect') as HTMLSelectElement;
      const confirmBtn = document.getElementById('confirmBtn');
      const cancelBtn = document.getElementById('cancelBtn');
      
      confirmBtn?.addEventListener('click', () => {
        const selectedId = parseInt(selectElement.value);
        const selected = adminLevels.find((l: any) => l.id === selectedId);
        document.body.removeChild(modal);
        resolve(selected);
      });
      
      cancelBtn?.addEventListener('click', () => {
        document.body.removeChild(modal);
        resolve(null);
      });
      
      // Allow ESC key to cancel
      const escHandler = (e: KeyboardEvent) => {
        if (e.key === 'Escape') {
          document.body.removeChild(modal);
          document.removeEventListener('keydown', escHandler);
          resolve(null);
        }
      };
      document.addEventListener('keydown', escHandler);
    });
    
    if (!adminLevel) {
      console.log('Admin import cancelled by user');
      return;
    }
    
    // Confirm import with selected level
    const confirmed = confirm(
      `📍 Import Admin Boundaries\n\n` +
      `Level: ${adminLevel.level} (${adminLevel.name})\n` +
      `Description: ${adminLevel.description || 'N/A'}\n\n` +
      `This will import all ${adminLevel.name} boundaries for this country.\n\n` +
      `Continue?`
    );
    
    if (!confirmed) {
      console.log('Admin import cancelled by user');
      return;
    }
    
    // Call generic handler with admin level parameter
    await handleGeoJSONImport('admin', fieldName, fieldValue, onChange, {
      adminLevelId: adminLevel.id,
      adminLevel: adminLevel.level
    });
    
  } catch (error) {
    console.error('Error fetching admin levels:', error);
    alert(`❌ Error: ${error instanceof Error ? error.message : 'Failed to fetch admin levels'}`);
  }
};

// ============================================================================
// Export (for TypeScript module system)
// ============================================================================

export {};
