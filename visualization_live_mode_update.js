// ============================================================================
// UPDATED VISUALIZATION CODE - Shows REAL passengers from database
// ============================================================================

// Replace the generateSpawningData() function with this:

/**
 * Show real active passengers from the database
 * This is the DEFAULT mode - shows actual passengers from simulation
 */
async function showLivePassengers() {
    console.log('🔴 LIVE MODE: Fetching real passengers from database...');
    
    // Clear existing layers
    Object.values(passengerLayers).forEach(layer => layer.clearLayers());
    
    let counts = { depot: 0, route: 0, poi: 0, total: 0 };
    let statusCounts = { WAITING: 0, ONBOARD: 0, COMPLETED: 0 };
    
    try {
        // Query REAL passengers from Strapi database
        const response = await fetch(`${CONFIG.API_BASE}/active-passengers?pagination[pageSize]=1000`);
        
        if (!response.ok) {
            console.error('Failed to fetch passengers:', response.status);
            return;
        }
        
        const data = await response.json();
        const passengers = data.data || [];
        
        console.log(`✅ Found ${passengers.length} real passengers in database`);
        
        // Render each real passenger on the map
        for (const passenger of passengers) {
            const lat = passenger.latitude;
            const lon = passenger.longitude;
            const status = passenger.status || 'WAITING';
            const depotId = passenger.depot_id;
            
            statusCounts[status] = (statusCounts[status] || 0) + 1;
            counts.total++;
            
            // Determine spawn type
            let spawnType = 'route'; // default
            if (depotId) {
                spawnType = 'depot';
                counts.depot++;
            } else {
                counts.route++; // Could also check for POI spawns
            }
            
            // Create marker with status-based styling
            const markerIcon = getPassengerIcon(status);
            const marker = L.marker([lat, lon], { icon: markerIcon });
            
            // Create detailed popup
            marker.bindPopup(`
                <div class="popup-custom">
                    <div class="location-type">${getStatusEmoji(status)} ${status} PASSENGER</div>
                    <div class="location-name">${passenger.passenger_id}</div>
                    <div class="spawn-info">
                        <strong>🚌 Route:</strong> ${passenger.route_id}<br>
                        <strong>📍 Direction:</strong> ${passenger.direction || 'N/A'}<br>
                        ${depotId ? `<strong>🏢 Depot:</strong> ${depotId}<br>` : ''}
                        <strong>📌 Current:</strong> (${lat.toFixed(4)}, ${lon.toFixed(4)})<br>
                        <strong>🎯 Destination:</strong> ${passenger.destination_name || 'Unknown'}<br>
                        <strong>⏰ Spawned:</strong> ${formatTime(passenger.spawned_at)}<br>
                        ${passenger.boarded_at ? `<strong>🚌 Boarded:</strong> ${formatTime(passenger.boarded_at)}<br>` : ''}
                        ${passenger.alighted_at ? `<strong>🚶 Alighted:</strong> ${formatTime(passenger.alighted_at)}<br>` : ''}
                        <strong>⏱️ Expires:</strong> ${formatTime(passenger.expires_at)}<br>
                        <strong>🎖️ Priority:</strong> ${passenger.priority || 3}
                    </div>
                </div>
            `);
            
            // Add to appropriate layer
            passengerLayers[spawnType].addLayer(marker);
        }
        
        // Update UI statistics
        document.getElementById('depotCount').textContent = counts.depot;
        document.getElementById('routeCount').textContent = counts.route;
        document.getElementById('poiCount').textContent = counts.poi || 0;
        document.getElementById('totalCount').textContent = counts.total;
        
        // Update status breakdown (add this to HTML if not exists)
        updateStatusBreakdown(statusCounts);
        
        console.log(`📊 Rendered ${counts.total} real passengers:`, counts);
        console.log(`📊 Status breakdown:`, statusCounts);
        
    } catch (error) {
        console.error('❌ Error fetching live passengers:', error);
    }
}

/**
 * Show historical passengers for a specific time range
 */
async function showHistoricalPassengers(startTime, endTime) {
    console.log(`📅 HISTORICAL MODE: ${startTime} to ${endTime}`);
    
    // Clear existing layers
    Object.values(passengerLayers).forEach(layer => layer.clearLayers());
    
    try {
        // Query passengers spawned in time range
        const url = `${CONFIG.API_BASE}/active-passengers?` +
            `filters[spawned_at][$gte]=${startTime}&` +
            `filters[spawned_at][$lt]=${endTime}&` +
            `pagination[pageSize]=1000`;
        
        const response = await fetch(url);
        const data = await response.json();
        const passengers = data.data || [];
        
        console.log(`✅ Found ${passengers.length} passengers in time range`);
        
        // Render passengers (same logic as showLivePassengers)
        passengers.forEach(passenger => {
            // ... same rendering code ...
        });
        
    } catch (error) {
        console.error('❌ Error fetching historical passengers:', error);
    }
}

/**
 * Filter passengers by current hour from time slider
 */
async function showPassengersForHour(hour) {
    const startTime = `2025-10-12T${String(hour).padStart(2, '0')}:00:00Z`;
    const endTime = `2025-10-12T${String(hour + 1).padStart(2, '0')}:00:00Z`;
    
    await showHistoricalPassengers(startTime, endTime);
}

/**
 * Get marker icon based on passenger status
 */
function getPassengerIcon(status) {
    const iconHtml = {
        'WAITING': '<i class="fas fa-user" style="color: #ff6b6b;"></i>',
        'ONBOARD': '<i class="fas fa-user-check" style="color: #4ecdc4;"></i>',
        'COMPLETED': '<i class="fas fa-user-check" style="color: #95a5a6;"></i>',
        'EXPIRED': '<i class="fas fa-user-times" style="color: #e74c3c;"></i>'
    };
    
    return L.divIcon({
        html: iconHtml[status] || iconHtml['WAITING'],
        iconSize: [20, 20],
        iconAnchor: [10, 10],
        className: `custom-passenger-icon status-${status.toLowerCase()}`
    });
}

/**
 * Get emoji for status
 */
function getStatusEmoji(status) {
    const emojis = {
        'WAITING': '🚶',
        'ONBOARD': '🚌',
        'COMPLETED': '✅',
        'EXPIRED': '⏰'
    };
    return emojis[status] || '❓';
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp) {
    if (!timestamp) return 'N/A';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Update status breakdown in UI
 */
function updateStatusBreakdown(statusCounts) {
    // Add this HTML section if it doesn't exist:
    // <div id="statusBreakdown" class="status-breakdown">
    //     <div>🚶 Waiting: <span id="waitingCount">0</span></div>
    //     <div>🚌 Onboard: <span id="onboardCount">0</span></div>
    //     <div>✅ Completed: <span id="completedCount">0</span></div>
    // </div>
    
    if (document.getElementById('waitingCount')) {
        document.getElementById('waitingCount').textContent = statusCounts.WAITING || 0;
        document.getElementById('onboardCount').textContent = statusCounts.ONBOARD || 0;
        document.getElementById('completedCount').textContent = statusCounts.COMPLETED || 0;
    }
}

/**
 * Auto-refresh live passengers every 5 seconds
 */
let autoRefreshInterval = null;

function startAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
    }
    
    // Refresh every 5 seconds
    autoRefreshInterval = setInterval(() => {
        console.log('🔄 Auto-refreshing live passengers...');
        showLivePassengers();
    }, 5000);
    
    console.log('✅ Auto-refresh enabled (every 5 seconds)');
}

function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
        console.log('⏸️ Auto-refresh disabled');
    }
}

/**
 * OPTIONAL: Keep prediction mode for capacity planning
 * This shows FORECASTED spawn points (not real passengers)
 */
async function generatePrediction(hour) {
    console.log(`📊 PREDICTION MODE: Forecasting for hour ${hour}...`);
    
    // Show warning to user
    showPredictionWarning();
    
    // Clear existing layers
    Object.values(passengerLayers).forEach(layer => layer.clearLayers());
    
    try {
        // Call the prediction API
        const response = await fetch(`${CONFIG.API_BASE}/passenger-spawning/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                hour: hour,
                time_window_minutes: 5,
                country_code: 'barbados'
            })
        });
        
        const data = await response.json();
        console.log(`✅ Generated ${data.spawn_requests?.length || 0} predicted spawn points`);
        
        // Render predicted spawn points (same as original code)
        // ... existing rendering code ...
        
    } catch (error) {
        console.error('❌ Error generating prediction:', error);
    }
}

function showPredictionWarning() {
    // Add warning banner to UI
    const banner = document.createElement('div');
    banner.className = 'prediction-warning';
    banner.innerHTML = '⚠️ PREDICTION MODE - Showing forecasted spawn points, not real passengers';
    banner.style.cssText = `
        position: fixed;
        top: 60px;
        left: 50%;
        transform: translateX(-50%);
        background: #f39c12;
        color: white;
        padding: 10px 20px;
        border-radius: 6px;
        font-weight: bold;
        z-index: 10000;
    `;
    document.body.appendChild(banner);
}

// ============================================================================
// UPDATED INITIALIZATION
// ============================================================================

/**
 * Initialize with LIVE mode by default
 */
async function init() {
    try {
        initializeMap();
        await loadBaseData();
        setupEventListeners();
        
        // DEFAULT: Show live passengers from database
        await showLivePassengers();
        
        // Start auto-refresh
        startAutoRefresh();
        
        hideLoading();
        updateDisplay();
    } catch (error) {
        console.error('Initialization failed:', error);
        document.getElementById('loading').innerHTML = 
            '<div style="color: red;">❌ Failed to load data. Please check API connection.</div>';
    }
}

/**
 * Update event listeners to use live mode
 */
function setupEventListeners() {
    // Time slider now shows historical passengers for that hour
    const timeSlider = document.getElementById('timeSlider');
    timeSlider.addEventListener('input', async (e) => {
        const hour = parseInt(e.target.value);
        currentHour = hour;
        updateTimeDisplay(hour);
        
        // Stop auto-refresh when scrubbing
        stopAutoRefresh();
        
        // Show passengers from that hour
        await showPassengersForHour(hour);
    });
    
    // Add "Back to Live" button
    const backToLiveBtn = document.createElement('button');
    backToLiveBtn.textContent = '🔴 Back to Live';
    backToLiveBtn.className = 'filter-btn';
    backToLiveBtn.onclick = () => {
        showLivePassengers();
        startAutoRefresh();
    };
    document.querySelector('.controls-panel').appendChild(backToLiveBtn);
    
    // Filter buttons work with live data
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.target.dataset.filter;
            toggleFilter(filter);
            updateDisplay(); // Re-render with filter
        });
    });
}
