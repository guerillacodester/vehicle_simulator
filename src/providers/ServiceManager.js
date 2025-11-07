// ServiceManager.js
// Centralized module to manage all services (gpscentcom_server, simulator, etc.)

class ServiceManager {
  constructor() {
    this.services = {
      gpscentcom: {
        status: 'stopped',
        startCommand: '/start-gpscentcom',
        stopCommand: '/stop-gpscentcom',
        statusEndpoint: '/status-gpscentcom',
      },
      simulator: {
        status: 'stopped',
        startCommand: '/start-simulator',
        stopCommand: '/stop-simulator',
        statusEndpoint: '/status-simulator',
      },
    };
  }

  async startService(serviceName) {
    const service = this.services[serviceName];
    if (!service) {
      throw new Error(`Service ${serviceName} not found.`);
    }

    try {
      // Simulate HTTP request to start the service
      console.log(`Starting ${serviceName}...`);
      service.status = 'running';
      return { success: true, message: `${serviceName} started successfully.` };
    } catch (error) {
      console.error(`Failed to start ${serviceName}:`, error);
      return { success: false, message: `Failed to start ${serviceName}.` };
    }
  }

  async stopService(serviceName) {
    const service = this.services[serviceName];
    if (!service) {
      throw new Error(`Service ${serviceName} not found.`);
    }

    try {
      // Simulate HTTP request to stop the service
      console.log(`Stopping ${serviceName}...`);
      service.status = 'stopped';
      return { success: true, message: `${serviceName} stopped successfully.` };
    } catch (error) {
      console.error(`Failed to stop ${serviceName}:`, error);
      return { success: false, message: `Failed to stop ${serviceName}.` };
    }
  }

  async getServiceStatus(serviceName) {
    const service = this.services[serviceName];
    if (!service) {
      throw new Error(`Service ${serviceName} not found.`);
    }

    try {
      // Simulate HTTP request to get the service status
      console.log(`Fetching status for ${serviceName}...`);
      return { success: true, status: service.status };
    } catch (error) {
      console.error(`Failed to fetch status for ${serviceName}:`, error);
      return { success: false, message: `Failed to fetch status for ${serviceName}.` };
    }
  }

  async getAllServiceStatuses() {
    try {
      const statuses = Object.keys(this.services).map((serviceName) => {
        const service = this.services[serviceName];
        return { serviceName, status: service.status };
      });

      console.log('Fetching statuses for all services...');
      return { success: true, statuses };
    } catch (error) {
      console.error('Failed to fetch statuses for all services:', error);
      return { success: false, message: 'Failed to fetch statuses for all services.' };
    }
  }
}

module.exports = new ServiceManager();