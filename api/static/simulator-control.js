/**
 * Simulator Control JavaScript
 * ===========================
 * Handles real-time simulator control and monitoring
 */

class SimulatorController {
    constructor() {
        this.isRunning = false;
        this.statusInterval = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.refreshStatus();
        this.loadCountries();
    }

    bindEvents() {
        // Form submission
        document.getElementById('start-simulation-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.startSimulation();
        });

        // Stop button
        document.getElementById('stop-btn').addEventListener('click', () => {
            this.stopSimulation();
        });

        // Refresh status button
        document.getElementById('refresh-status').addEventListener('click', () => {
            this.refreshStatus();
        });
    }

    async loadCountries() {
        try {
            const response = await fetch('/fleet/countries');
            const countries = await response.json();
            
            const countrySelect = document.getElementById('country');
            countrySelect.innerHTML = '<option value="">All Countries</option>';
            
            // Handle CountryData objects with country property
            countries.forEach(countryData => {
                const option = document.createElement('option');
                option.value = countryData.country.toLowerCase();
                option.textContent = countryData.country.charAt(0).toUpperCase() + countryData.country.slice(1);
                countrySelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error loading countries:', error);
            // Fallback to static list if API fails
            const countrySelect = document.getElementById('country');
            countrySelect.innerHTML = `
                <option value="">All Countries</option>
                <option value="barbados">Barbados</option>
                <option value="trinidad">Trinidad & Tobago</option>
                <option value="jamaica">Jamaica</option>
            `;
        }
    }

    async startSimulation() {
        const form = document.getElementById('start-simulation-form');
        const formData = new FormData(form);
        
        const request = {
            country: formData.get('country') || null,
            duration_seconds: parseInt(formData.get('duration_seconds')),
            update_interval: parseFloat(formData.get('update_interval')),
            gps_enabled: formData.get('gps_enabled') === 'on'
        };

        try {
            this.showMessage('Starting simulation...', 'info');
            
            const response = await fetch('/simulator/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(request)
            });

            if (response.ok) {
                const result = await response.json();
                this.showMessage('Simulation started successfully!', 'success');
                this.updateUI(true);
                this.startStatusPolling();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            this.showMessage(`Error starting simulation: ${error.message}`, 'error');
        }
    }

    async stopSimulation() {
        try {
            this.showMessage('Stopping simulation...', 'info');
            
            const response = await fetch('/simulator/stop', {
                method: 'POST'
            });

            if (response.ok) {
                this.showMessage('Simulation stopped successfully!', 'success');
                this.updateUI(false);
                this.stopStatusPolling();
            } else {
                const error = await response.json();
                this.showMessage(`Error: ${error.detail}`, 'error');
            }
        } catch (error) {
            this.showMessage(`Error stopping simulation: ${error.message}`, 'error');
        }
    }

    async refreshStatus() {
        try {
            const response = await fetch('/simulator/status');
            const status = await response.json();
            
            this.isRunning = status.is_running;
            this.updateStatusDisplay(status);
            this.updateUI(this.isRunning);
            
            if (this.isRunning) {
                this.loadActiveVehicles();
                if (!this.statusInterval) {
                    this.startStatusPolling();
                }
            } else {
                this.stopStatusPolling();
            }
        } catch (error) {
            console.error('Error refreshing status:', error);
        }
    }

    async loadActiveVehicles() {
        try {
            const response = await fetch('/simulator/vehicles');
            const vehicles = await response.json();
            
            this.displayVehicles(vehicles);
        } catch (error) {
            console.error('Error loading vehicles:', error);
        }
    }

    updateStatusDisplay(status) {
        const indicator = document.getElementById('status-indicator');
        const details = document.getElementById('simulation-details');
        
        if (status.is_running) {
            indicator.className = 'status-indicator status-running';
            indicator.innerHTML = '<i class="fas fa-play-circle"></i><span>Running</span>';
            
            details.style.display = 'block';
            document.getElementById('sim-duration').textContent = `${status.duration_seconds}s`;
            document.getElementById('sim-vehicles').textContent = status.active_vehicles || 0;
            document.getElementById('sim-country').textContent = status.country || 'All';
            document.getElementById('sim-gps').textContent = status.gps_enabled ? 'Yes' : 'No';
        } else {
            indicator.className = 'status-indicator status-stopped';
            indicator.innerHTML = '<i class="fas fa-stop-circle"></i><span>Stopped</span>';
            details.style.display = 'none';
        }
    }

    displayVehicles(vehicles) {
        const container = document.getElementById('vehicles-container');
        
        if (!vehicles || vehicles.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted">
                    <i class="fas fa-bus fa-3x mb-3"></i>
                    <p>No active vehicles. Start a simulation to see vehicles here.</p>
                </div>
            `;
            return;
        }

        container.innerHTML = `
            <div class="row">
                ${vehicles.map(vehicle => `
                    <div class="col-md-6 col-lg-4 mb-3">
                        <div class="card border-0 shadow-sm">
                            <div class="card-body">
                                <h6 class="card-title">
                                    <i class="fas fa-bus text-primary me-2"></i>
                                    ${vehicle.vehicle_id}
                                </h6>
                                <p class="card-text small">
                                    <strong>Route:</strong> ${vehicle.route_name || 'Unknown'}<br>
                                    <strong>Position:</strong> ${vehicle.latitude}, ${vehicle.longitude}<br>
                                    <strong>Status:</strong> <span class="badge bg-success">${vehicle.status}</span>
                                </p>
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    }

    updateUI(isRunning) {
        const startBtn = document.getElementById('start-btn');
        const stopBtn = document.getElementById('stop-btn');
        const form = document.getElementById('start-simulation-form');
        
        if (isRunning) {
            startBtn.disabled = true;
            stopBtn.disabled = false;
            
            // Disable form inputs
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => input.disabled = true);
        } else {
            startBtn.disabled = false;
            stopBtn.disabled = true;
            
            // Enable form inputs
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => input.disabled = false);
        }
    }

    startStatusPolling() {
        if (this.statusInterval) return;
        
        this.statusInterval = setInterval(() => {
            this.refreshStatus();
        }, 2000); // Poll every 2 seconds
    }

    stopStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    showMessage(message, type) {
        const container = document.getElementById('status-messages');
        const id = 'msg-' + Date.now();
        
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'info': 'alert-info',
            'warning': 'alert-warning'
        }[type] || 'alert-info';
        
        const alertHtml = `
            <div id="${id}" class="alert ${alertClass} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        container.insertAdjacentHTML('beforeend', alertHtml);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const element = document.getElementById(id);
            if (element) {
                element.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new SimulatorController();
});
