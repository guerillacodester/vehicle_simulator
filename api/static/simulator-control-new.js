// Simulator Control JavaScript - Updated for GTFS API Integration

class SimulatorControl {
    constructor() {
        this.isRunning = false;
        this.startTime = null;
        this.statusInterval = null;
        
        this.init();
    }

    async init() {
        this.setupEventListeners();
        await this.updateStatus();
        this.startStatusPolling();
    }

    setupEventListeners() {
        document.getElementById('start-simulator-btn').addEventListener('click', () => {
            this.startSimulator();
        });

        document.getElementById('stop-simulator-btn').addEventListener('click', () => {
            this.stopSimulator();
        });

        // Auto-refresh status every 2 seconds
        setInterval(() => {
            if (this.isRunning) {
                this.updateRuntime();
            }
        }, 1000);
    }

    async startSimulator() {
        const startBtn = document.getElementById('start-simulator-btn');
        const stopBtn = document.getElementById('stop-simulator-btn');

        try {
            startBtn.disabled = true;
            startBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Starting...';

            const config = {
                tick: parseFloat(document.getElementById('tick-interval').value),
                seconds: parseInt(document.getElementById('duration').value),
                debug: document.getElementById('debug-mode').checked,
                no_gps: document.getElementById('no-gps').checked
            };

            const response = await fetch('/api/v1/simulator/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });

            if (response.ok) {
                const result = await response.json();
                this.showNotification('Simulator started successfully!', 'success');
                this.isRunning = true;
                this.startTime = Date.now();
                
                startBtn.disabled = true;
                stopBtn.disabled = false;
                
                await this.updateStatus();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start simulator');
            }
        } catch (error) {
            console.error('Error starting simulator:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            startBtn.innerHTML = '<i class="fas fa-play me-2"></i>Start Simulation';
            startBtn.disabled = this.isRunning;
        }
    }

    async stopSimulator() {
        const startBtn = document.getElementById('start-simulator-btn');
        const stopBtn = document.getElementById('stop-simulator-btn');

        try {
            stopBtn.disabled = true;
            stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Stopping...';

            const response = await fetch('/api/v1/simulator/stop', {
                method: 'POST'
            });

            if (response.ok) {
                this.showNotification('Simulator stopped successfully!', 'success');
                this.isRunning = false;
                this.startTime = null;
                
                startBtn.disabled = false;
                stopBtn.disabled = true;
                
                await this.updateStatus();
            } else {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to stop simulator');
            }
        } catch (error) {
            console.error('Error stopping simulator:', error);
            this.showNotification(`Error: ${error.message}`, 'error');
        } finally {
            stopBtn.innerHTML = '<i class="fas fa-stop me-2"></i>Stop Simulation';
            stopBtn.disabled = !this.isRunning;
        }
    }

    async updateStatus() {
        try {
            const response = await fetch('/api/v1/simulator/status');
            if (response.ok) {
                const status = await response.json();
                this.displayStatus(status);
                
                // Update local state
                this.isRunning = status.running;
                this.startTime = status.start_time ? status.start_time * 1000 : null;
                
                // Update button states
                document.getElementById('start-simulator-btn').disabled = status.running;
                document.getElementById('stop-simulator-btn').disabled = !status.running;
            }
        } catch (error) {
            console.error('Error fetching simulator status:', error);
        }
    }

    displayStatus(status) {
        const statusIndicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        const processIdText = document.getElementById('process-id-text');
        const lastUpdateText = document.getElementById('last-update-text');

        if (status.running) {
            statusIndicator.innerHTML = '<i class="fas fa-circle text-success"></i>';
            statusText.textContent = 'Running';
            processIdText.textContent = status.process_id || '-';
        } else {
            statusIndicator.innerHTML = '<i class="fas fa-circle text-secondary"></i>';
            statusText.textContent = 'Stopped';
            processIdText.textContent = '-';
        }

        lastUpdateText.textContent = new Date().toLocaleTimeString();

        // Update runtime
        this.updateRuntime();
    }

    updateRuntime() {
        const runtimeText = document.getElementById('runtime-text');
        
        if (this.isRunning && this.startTime) {
            const elapsed = Math.floor((Date.now() - this.startTime) / 1000);
            const hours = Math.floor(elapsed / 3600);
            const minutes = Math.floor((elapsed % 3600) / 60);
            const seconds = elapsed % 60;
            
            runtimeText.textContent = `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        } else {
            runtimeText.textContent = '00:00:00';
        }
    }

    startStatusPolling() {
        this.statusInterval = setInterval(async () => {
            await this.updateStatus();
        }, 5000); // Poll every 5 seconds
    }

    showNotification(message, type = 'info') {
        // Try to find existing notification container
        let container = document.getElementById('status-messages');
        if (!container) {
            // Create notification container if it doesn't exist
            container = document.createElement('div');
            container.id = 'status-messages';
            container.className = 'position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '1050';
            document.body.appendChild(container);
        }
        
        const notificationId = 'notification-' + Date.now();
        
        const alertClass = type === 'success' ? 'alert-success' : 
                          type === 'error' ? 'alert-danger' : 'alert-info';
        
        const notification = document.createElement('div');
        notification.id = notificationId;
        notification.className = `alert ${alertClass} alert-dismissible fade show`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        container.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const element = document.getElementById(notificationId);
            if (element) {
                element.remove();
            }
        }, 5000);
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.simulatorControl = new SimulatorControl();
});
