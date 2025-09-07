// Fleet Management Professional Interface JavaScript

class FleetManagement {
    constructor() {
        this.selectedCountry = null;
        this.countries = [];
        this.uploadProgress = {};
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.setupDragAndDrop();
        await this.loadCountries();
        this.updateSummaryCards();
    }

    setupEventListeners() {
        // File input change events
        document.getElementById('routes-files').addEventListener('change', (e) => {
            this.handleFileSelection(e, 'routes');
        });
        
        document.getElementById('vehicles-files').addEventListener('change', (e) => {
            this.handleFileSelection(e, 'vehicles');
        });
        
        document.getElementById('timetables-files').addEventListener('change', (e) => {
            this.handleFileSelection(e, 'timetables');
        });

        // Form submissions
        document.getElementById('routes-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadFiles('routes');
        });
        
        document.getElementById('vehicles-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadFiles('vehicles');
        });
        
        document.getElementById('timetables-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.uploadFiles('timetables');
        });

        // Country selection
        document.getElementById('add-country-btn').addEventListener('click', () => {
            const countryInput = document.getElementById('country-input');
            const country = countryInput.value.trim().toLowerCase();
            if (country) {
                this.selectCountry(country);
                countryInput.value = '';
            }
        });

        // Enter key for country input
        document.getElementById('country-input').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                document.getElementById('add-country-btn').click();
            }
        });

        // CRUD modal event listeners
        document.getElementById('add-new-country-btn').addEventListener('click', () => {
            this.openCountryModal();
        });

        document.getElementById('save-country-btn').addEventListener('click', () => {
            this.saveCountry();
        });
    }

    setupDragAndDrop() {
        const dropzones = ['routes-dropzone', 'vehicles-dropzone', 'timetables-dropzone'];
        
        dropzones.forEach(zoneId => {
            const zone = document.getElementById(zoneId);
            const fileType = zoneId.split('-')[0];
            
            zone.addEventListener('dragover', (e) => {
                e.preventDefault();
                zone.classList.add('dragover');
            });
            
            zone.addEventListener('dragleave', (e) => {
                e.preventDefault();
                zone.classList.remove('dragover');
            });
            
            zone.addEventListener('drop', (e) => {
                e.preventDefault();
                zone.classList.remove('dragover');
                
                const files = Array.from(e.dataTransfer.files);
                this.handleDroppedFiles(files, fileType);
            });
            
            zone.addEventListener('click', () => {
                document.getElementById(`${fileType}-files`).click();
            });
        });
    }

    handleFileSelection(event, type) {
        const files = Array.from(event.target.files);
        this.displayFiles(files, type);
        this.validateUpload(type);
    }

    handleDroppedFiles(files, type) {
        // Validate file types
        const validExtension = type === 'routes' ? '.geojson' : '.json';
        const validFiles = files.filter(file => file.name.toLowerCase().endsWith(validExtension));
        
        if (validFiles.length !== files.length) {
            this.showNotification(`Some files were ignored. Only ${validExtension} files are allowed for ${type}.`, 'warning');
        }
        
        if (validFiles.length > 0) {
            // Update file input
            const input = document.getElementById(`${type}-files`);
            const dt = new DataTransfer();
            validFiles.forEach(file => dt.items.add(file));
            input.files = dt.files;
            
            this.displayFiles(validFiles, type);
            this.validateUpload(type);
        }
    }

    displayFiles(files, type) {
        const container = document.getElementById(`${type}-file-list`);
        container.innerHTML = '';
        
        files.forEach((file, index) => {
            const fileItem = document.createElement('div');
            fileItem.className = 'file-item fade-in';
            fileItem.innerHTML = `
                <div class="file-info">
                    <div class="file-name">
                        <i class="fas fa-file me-2"></i>${file.name}
                    </div>
                    <div class="file-size">${this.formatFileSize(file.size)}</div>
                </div>
                <div class="file-status">
                    <button type="button" class="btn btn-sm btn-outline-danger" onclick="fleetMgmt.removeFile('${type}', ${index})">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            container.appendChild(fileItem);
        });
    }

    removeFile(type, index) {
        const input = document.getElementById(`${type}-files`);
        const dt = new DataTransfer();
        
        Array.from(input.files).forEach((file, i) => {
            if (i !== index) dt.items.add(file);
        });
        
        input.files = dt.files;
        this.displayFiles(Array.from(input.files), type);
        this.validateUpload(type);
    }

    validateUpload(type) {
        const input = document.getElementById(`${type}-files`);
        const button = document.getElementById(`upload-${type}-btn`);
        const country = document.getElementById('country-input').value.trim();
        
        const hasFiles = input.files.length > 0;
        const hasCountry = country.length > 0;
        
        button.disabled = !(hasFiles && hasCountry);
        
        if (hasFiles && !hasCountry) {
            this.showNotification('Please enter a country name before uploading.', 'warning');
        }
    }

    async uploadFiles(type) {
        const country = document.getElementById('country-input').value.trim().toLowerCase();
        const input = document.getElementById(`${type}-files`);
        
        if (!country || input.files.length === 0) {
            this.showNotification('Please select a country and files to upload.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('country', country);
        
        Array.from(input.files).forEach(file => {
            formData.append(`${type}_files`, file);
        });

        try {
            this.showProgressModal();
            this.updateProgress(0, `Uploading ${input.files.length} ${type} file(s)...`);
            
            const response = await fetch(`/fleet/upload/${type}`, {
                method: 'POST',
                body: formData
            });

            this.updateProgress(100, 'Upload complete!');
            
            if (response.ok) {
                const result = await response.json();
                this.showNotification(`Successfully uploaded ${result.files_processed} ${type} file(s) for ${country}!`, 'success');
                
                // Clear form
                input.value = '';
                document.getElementById(`${type}-file-list`).innerHTML = '';
                document.getElementById(`upload-${type}-btn`).disabled = true;
                
                // Refresh data
                await this.loadCountries();
                this.selectCountry(country);
                this.updateSummaryCards();
                
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Upload failed');
            }
            
        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification(`Upload failed: ${error.message}`, 'error');
        } finally {
            setTimeout(() => {
                this.hideProgressModal();
            }, 1000);
        }
    }

    async loadCountries() {
        try {
            // Use GTFS API endpoint instead of fleet endpoint
            const response = await fetch('/api/v1/countries');
            if (response.ok) {
                this.countries = await response.json();
                this.displayCountries();
            } else {
                throw new Error('Failed to load countries');
            }
        } catch (error) {
            console.error('Error loading countries:', error);
            this.showNotification('Failed to load countries data.', 'error');
        }
    }

    displayCountries() {
        const container = document.getElementById('countries-list');
        
        if (this.countries.length === 0) {
            container.innerHTML = `
                <div class="text-center p-3 text-muted">
                    <i class="fas fa-globe fa-2x mb-2"></i>
                    <p>No countries found.<br>Add a new country to get started!</p>
                </div>
            `;
            return;
        }

        container.innerHTML = '';
        
        this.countries.forEach(country => {
            const item = document.createElement('div');
            item.className = 'list-group-item country-item';
            
            item.innerHTML = `
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1" style="cursor: pointer;" 
                         onclick="window.fleetMgmt.selectCountry('${country.iso_code}')">
                        <h6 class="mb-1">
                            <i class="fas fa-flag me-2"></i>${country.name}
                        </h6>
                        <small class="text-muted">ISO: ${country.iso_code}</small>
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" 
                                onclick="window.fleetMgmt.openCountryModal(${JSON.stringify(country).replace(/"/g, '&quot;')})" 
                                title="Edit Country">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn btn-outline-danger" 
                                onclick="window.fleetMgmt.deleteCountry('${country.country_id}', '${country.name}')" 
                                title="Delete Country">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
            
            container.appendChild(item);
        });
    }

    async selectCountry(countryName) {
        this.selectedCountry = countryName;
        
        // Update country input
        document.getElementById('country-input').value = countryName;
        
        // Update active state
        document.querySelectorAll('.country-item').forEach(item => {
            item.classList.remove('active');
        });
        
        const activeItem = Array.from(document.querySelectorAll('.country-item'))
            .find(item => item.textContent.toLowerCase().includes(countryName.toLowerCase()));
        if (activeItem) {
            activeItem.classList.add('active');
        }
        
        // Load country details
        await this.loadCountryDetails(countryName);
        
        // Validate all upload forms
        ['routes', 'vehicles', 'timetables'].forEach(type => {
            this.validateUpload(type);
        });
    }

    async loadCountryDetails(country) {
        try {
            // Use GTFS API endpoints instead of fleet endpoints
            const [routesResponse, vehiclesResponse] = await Promise.all([
                fetch(`/api/v1/routes?country=${country}`),
                fetch(`/api/v1/vehicles?country=${country}`)
            ]);
            
            if (routesResponse.ok && vehiclesResponse.ok) {
                const routes = await routesResponse.json();
                const vehicles = await vehiclesResponse.json();
                
                this.displayCountryDetails(country, routes, vehicles);
            }
        } catch (error) {
            console.error('Error loading country details:', error);
        }
    }

    displayCountryDetails(country, routes, vehicles) {
        document.getElementById('selected-country').textContent = country.toUpperCase();
        
        const routesContainer = document.getElementById('country-routes');
        const vehiclesContainer = document.getElementById('country-vehicles');
        
        // Display routes
        if (routes && routes.length > 0) {
            routesContainer.innerHTML = routes.map(route => `
                <div class="mb-2 p-2 border rounded">
                    <strong>${route.route_id}</strong><br>
                    <small class="text-muted">
                        ${route.name} • ${route.vehicle_count} vehicles assigned
                        ${route.has_geometry ? ' • <i class="fas fa-map text-success"></i> Mapped' : ' • <i class="fas fa-map text-muted"></i> No map data'}
                    </small>
                </div>
            `).join('');
        } else {
            routesContainer.innerHTML = '<p class="text-muted">No routes uploaded yet.</p>';
        }
        
        // Display vehicles
        if (vehicles && vehicles.length > 0) {
            vehiclesContainer.innerHTML = vehicles.map(vehicle => `
                <div class="mb-2 p-2 border rounded">
                    <strong>${vehicle.vehicle_id}</strong><br>
                    <small class="text-muted">
                        Status: <span class="badge bg-${vehicle.status === 'available' ? 'success' : vehicle.status === 'in_service' ? 'primary' : 'secondary'}">${vehicle.status}</span>
                        ${vehicle.route_name ? ` • Route: ${vehicle.route_name}` : ' • No route assigned'}
                    </small>
                </div>
            `).join('');
        } else {
            vehiclesContainer.innerHTML = '<p class="text-muted">No vehicles uploaded yet.</p>';
        }
        
        document.getElementById('country-details').style.display = 'block';
        document.getElementById('country-details').classList.add('fade-in');
    }

    async updateSummaryCards() {
        try {
            // Fetch totals from GTFS API endpoints
            const [countriesResponse, routesResponse, vehiclesResponse, timetablesResponse] = await Promise.all([
                fetch('/api/v1/countries'),
                fetch('/api/v1/routes'),
                fetch('/api/v1/vehicles'),
                fetch('/api/v1/timetables')
            ]);
            
            const countries = countriesResponse.ok ? await countriesResponse.json() : [];
            const routes = routesResponse.ok ? await routesResponse.json() : [];
            const vehicles = vehiclesResponse.ok ? await vehiclesResponse.json() : [];
            const timetables = timetablesResponse.ok ? await timetablesResponse.json() : [];
            
            document.getElementById('total-countries').textContent = countries.length;
            document.getElementById('total-routes').textContent = routes.length;
            document.getElementById('total-vehicles').textContent = vehicles.length;
            document.getElementById('total-timetables').textContent = timetables.length;
        } catch (error) {
            console.error('Error updating summary cards:', error);
            // Set defaults if API calls fail
            document.getElementById('total-countries').textContent = '0';
            document.getElementById('total-routes').textContent = '0';
            document.getElementById('total-vehicles').textContent = '0';
            document.getElementById('total-timetables').textContent = '0';
        }
    }

    showProgressModal() {
        const modal = new bootstrap.Modal(document.getElementById('progressModal'));
        modal.show();
    }

    hideProgressModal() {
        const modal = bootstrap.Modal.getInstance(document.getElementById('progressModal'));
        if (modal) modal.hide();
    }

    updateProgress(percent, message) {
        document.getElementById('upload-progress').style.width = `${percent}%`;
        document.getElementById('upload-status').textContent = message;
    }

    showNotification(message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const toastBody = document.getElementById('toast-message');
        
        toast.className = `toast ${type}`;
        toastBody.textContent = message;
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }

    // CRUD Operations for Countries
    openCountryModal(country = null) {
        const modal = new bootstrap.Modal(document.getElementById('countryModal'));
        const title = document.getElementById('countryModalTitle');
        const saveBtn = document.getElementById('save-country-btn');
        
        if (country) {
            title.innerHTML = '<i class="fas fa-edit me-2"></i>Edit Country';
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Update Country';
            document.getElementById('country-iso-code').value = country.iso_code;
            document.getElementById('country-name').value = country.name;
            saveBtn.setAttribute('data-country-id', country.country_id);
        } else {
            title.innerHTML = '<i class="fas fa-plus me-2"></i>Add New Country';
            saveBtn.innerHTML = '<i class="fas fa-save me-1"></i>Save Country';
            document.getElementById('country-form').reset();
            saveBtn.removeAttribute('data-country-id');
        }
        
        modal.show();
    }

    async saveCountry() {
        const isoCode = document.getElementById('country-iso-code').value.trim().toUpperCase();
        const name = document.getElementById('country-name').value.trim();
        const saveBtn = document.getElementById('save-country-btn');
        const countryId = saveBtn.getAttribute('data-country-id');
        
        if (!isoCode || !name) {
            this.showNotification('Please fill in all required fields', 'error');
            return;
        }

        try {
            saveBtn.disabled = true;
            
            const payload = { iso_code: isoCode, name: name };
            let response;
            
            if (countryId) {
                // Update existing country
                response = await fetch(`/api/v1/countries/${countryId}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            } else {
                // Create new country
                response = await fetch('/api/v1/countries', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
            }
            
            if (response.ok) {
                const modal = bootstrap.Modal.getInstance(document.getElementById('countryModal'));
                modal.hide();
                this.showNotification(
                    countryId ? 'Country updated successfully' : 'Country created successfully', 
                    'success'
                );
                await this.loadCountries();
                await this.updateSummaryCards();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save country');
            }
        } catch (error) {
            console.error('Error saving country:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            saveBtn.disabled = false;
        }
    }

    async deleteCountry(countryId, countryName) {
        if (!confirm(`Are you sure you want to delete "${countryName}"? This action cannot be undone.`)) {
            return;
        }

        try {
            const response = await fetch(`/api/v1/countries/${countryId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showNotification('Country deleted successfully', 'success');
                await this.loadCountries();
                await this.updateSummaryCards();
            } else {
                throw new Error('Failed to delete country');
            }
        } catch (error) {
            console.error('Error deleting country:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDate(dateString) {
        if (!dateString) return 'Unknown';
        const date = new Date(dateString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.fleetMgmt = new FleetManagement();
});

// Global functions for onclick handlers
function removeFile(type, index) {
    window.fleetMgmt.removeFile(type, index);
}
