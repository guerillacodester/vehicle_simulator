/**
 * CENTRALIZED DATA PROVIDER
 * Handles all communication with the remote database API
 * Provides a single source of truth for data access across the application
 */

import axios, { AxiosInstance, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { 
  Vehicle, 
  Driver, 
  Route, 
  Stop, 
  VehicleStatus, 
  DriverStatus 
} from '@/domain/entities';

// Extend Axios config to include metadata
interface ExtendedAxiosRequestConfig extends InternalAxiosRequestConfig {
  metadata?: {
    startTime: number;
  };
}

// API Response interfaces
interface ApiResponse<T> {
  data: T;
  status: number;
  message?: string;
}

interface ApiErrorResponse {
  message?: string;
  detail?: string;
  error?: string;
}

interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
  hasNext: boolean;
  hasPrev: boolean;
}

// Configuration interface
interface DataProviderConfig {
  baseURL: string;
  timeout?: number;
  retryAttempts?: number;
  enableLogging?: boolean;
}

// Default configuration
const DEFAULT_CONFIG: DataProviderConfig = {
  baseURL: 'http://localhost:8000',
  timeout: 10000,
  retryAttempts: 3,
  enableLogging: true
};

class CentralizedDataProvider {
  private static instance: CentralizedDataProvider;
  private client: AxiosInstance;
  private config: DataProviderConfig;
  private retryCount = new Map<string, number>();

  private constructor(config: DataProviderConfig = DEFAULT_CONFIG) {
    this.config = { ...DEFAULT_CONFIG, ...config };
    this.client = this.createAxiosInstance();
  }

  static getInstance(config?: DataProviderConfig): CentralizedDataProvider {
    if (!CentralizedDataProvider.instance) {
      CentralizedDataProvider.instance = new CentralizedDataProvider(config);
    }
    return CentralizedDataProvider.instance;
  }

  private createAxiosInstance(): AxiosInstance {
    const instance = axios.create({
      baseURL: this.config.baseURL,
      timeout: this.config.timeout,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'X-Client': 'Fleet-Management-UI',
        'X-Version': '1.0.0'
      }
    });

    // Request interceptor for logging and authentication
    instance.interceptors.request.use(
      (config: ExtendedAxiosRequestConfig) => {
        if (this.config.enableLogging) {
          console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
        }
        
        // Add timestamp for request tracking
        config.metadata = { startTime: Date.now() };
        return config;
      },
      (error) => {
        console.error('🚨 Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor for logging and error handling
    instance.interceptors.response.use(
      (response: AxiosResponse) => {
        if (this.config.enableLogging) {
          const config = response.config as ExtendedAxiosRequestConfig;
          const duration = Date.now() - (config.metadata?.startTime || 0);
          console.log(`✅ API Response: ${response.status} in ${duration}ms`);
        }
        return response;
      },
      async (error: AxiosError) => {
        return this.handleError(error);
      }
    );

    return instance;
  }

  private async handleError(error: AxiosError): Promise<never> {
    const requestKey = `${error.config?.method}-${error.config?.url}`;
    const currentRetries = this.retryCount.get(requestKey) || 0;

    // Log error details
    if (error.response) {
      console.error(`🚨 API Error: ${error.response.status} - ${error.response.statusText}`);
      console.error(`📍 URL: ${error.config?.url}`);
      console.error(`📊 Data:`, error.response.data);
    } else if (error.request) {
      console.error('🚨 Network Error: No response received');
      console.error(`📍 URL: ${error.config?.url}`);
    } else {
      console.error('🚨 Request Setup Error:', error.message);
    }

    // Retry logic for certain types of errors
    if (
      currentRetries < (this.config.retryAttempts || 3) &&
      this.shouldRetry(error)
    ) {
      this.retryCount.set(requestKey, currentRetries + 1);
      console.log(`🔄 Retrying request... Attempt ${currentRetries + 1}`);
      
      // Exponential backoff
      const delay = Math.pow(2, currentRetries) * 1000;
      await new Promise(resolve => setTimeout(resolve, delay));
      
      return this.client.request(error.config!);
    }

    // Clear retry count after final attempt
    this.retryCount.delete(requestKey);

    // Transform error for domain layer
    throw this.transformError(error);
  }

  private shouldRetry(error: AxiosError): boolean {
    // Retry on network errors or 5xx server errors
    return !error.response || (error.response.status >= 500);
  }

  private transformError(error: AxiosError): Error {
    if (error.response?.status === 404) {
      // Check if this is an empty collection vs missing resource
      const errorData = error.response.data as ApiErrorResponse;
      if (errorData?.detail === 'Not Found') {
        // This might be an empty collection, not an actual error
        console.warn('API returned empty collection for:', error.config?.url);
        return new Error('EMPTY_COLLECTION');
      }
      return new Error('Resource not found');
    }
    if (error.response?.status === 400) {
      const errorData = error.response.data as ApiErrorResponse;
      const message = errorData?.message || errorData?.detail || 'Invalid request';
      return new Error(message);
    }
    if (error.response?.status === 401) {
      return new Error('Authentication required');
    }
    if (error.response?.status === 403) {
      return new Error('Access denied');
    }
    if (error.response?.status && error.response.status >= 500) {
      return new Error('Server error - please try again later');
    }
    return new Error(error.message || 'Network error');
  }

  // Health check method
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      console.error('❌ Health check failed:', error);
      return false;
    }
  }

  // Generic HTTP methods
  async get<T>(endpoint: string, params?: Record<string, any>): Promise<T> {
    const response = await this.client.get<T>(endpoint, { params });
    return response.data;
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.client.post<T>(endpoint, data);
    return response.data;
  }

  async put<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.client.put<T>(endpoint, data);
    return response.data;
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    const response = await this.client.patch<T>(endpoint, data);
    return response.data;
  }

  async delete(endpoint: string): Promise<void> {
    await this.client.delete(endpoint);
  }

  // Vehicle-specific methods
  async getVehicles(): Promise<Vehicle[]> {
    try {
      return await this.get<Vehicle[]>('/api/v1/vehicles');
    } catch (error) {
      if (error instanceof Error && error.message === 'EMPTY_COLLECTION') {
        console.log('📋 No vehicles found in database, returning empty array');
        return [];
      }
      throw error;
    }
  }

  async getVehicleById(id: string): Promise<Vehicle> {
    return this.get<Vehicle>(`/api/v1/vehicles/${id}`);
  }

  async createVehicle(vehicle: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>): Promise<Vehicle> {
    return this.post<Vehicle>('/api/v1/vehicles', vehicle);
  }

  async updateVehicle(id: string, vehicle: Partial<Vehicle>): Promise<Vehicle> {
    return this.put<Vehicle>(`/api/v1/vehicles/${id}`, vehicle);
  }

  async deleteVehicle(id: string): Promise<void> {
    return this.delete(`/api/v1/vehicles/${id}`);
  }

  // Driver-specific methods
  async getDrivers(): Promise<Driver[]> {
    try {
      return await this.get<Driver[]>('/api/v1/drivers');
    } catch (error) {
      if (error instanceof Error && error.message === 'EMPTY_COLLECTION') {
        console.log('📋 No drivers found in database, returning empty array');
        return [];
      }
      throw error;
    }
  }

  async getDriverById(id: string): Promise<Driver> {
    return this.get<Driver>(`/api/v1/drivers/${id}`);
  }

  async createDriver(driver: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>): Promise<Driver> {
    return this.post<Driver>('/api/v1/drivers', driver);
  }

  async updateDriver(id: string, driver: Partial<Driver>): Promise<Driver> {
    return this.put<Driver>(`/api/v1/drivers/${id}`, driver);
  }

  async deleteDriver(id: string): Promise<void> {
    return this.delete(`/api/v1/drivers/${id}`);
  }

  // Route-specific methods
  async getRoutes(): Promise<Route[]> {
    try {
      return await this.get<Route[]>('/api/v1/routes');
    } catch (error) {
      if (error instanceof Error && error.message === 'EMPTY_COLLECTION') {
        console.log('📋 No routes found in database, returning empty array');
        return [];
      }
      throw error;
    }
  }

  async getRouteById(id: string): Promise<Route> {
    return this.get<Route>(`/api/v1/routes/${id}`);
  }

  // Stop-specific methods
  async getStops(): Promise<Stop[]> {
    try {
      return await this.get<Stop[]>('/api/v1/stops');
    } catch (error) {
      if (error instanceof Error && error.message === 'EMPTY_COLLECTION') {
        console.log('📋 No stops found in database, returning empty array');
        return [];
      }
      throw error;
    }
  }

  async getStopById(id: string): Promise<Stop> {
    return this.get<Stop>(`/api/v1/stops/${id}`);
  }

  // Dashboard data methods
  async getDashboardStats(): Promise<{
    vehicleStats: {
      total: number;
      active: number;
      maintenance: number;
      outOfService: number;
    };
    driverStats: {
      total: number;
      available: number;
      onDuty: number;
      onLeave: number;
    };
    routeStats: {
      total: number;
      active: number;
    };
  }> {
    // Get all data in parallel
    const [vehicles, drivers, routes] = await Promise.all([
      this.getVehicles(),
      this.getDrivers(),
      this.getRoutes()
    ]);

    // Calculate statistics
    const vehicleStats = {
      total: vehicles.length,
      active: vehicles.filter(v => v.status === VehicleStatus.ACTIVE).length,
      maintenance: vehicles.filter(v => v.status === VehicleStatus.MAINTENANCE).length,
      outOfService: vehicles.filter(v => v.status === VehicleStatus.OUT_OF_SERVICE).length
    };

    const driverStats = {
      total: drivers.length,
      available: drivers.filter(d => d.status === DriverStatus.ACTIVE).length,
      onDuty: drivers.filter(d => d.status === DriverStatus.ACTIVE).length, // TODO: Distinguish from available
      onLeave: drivers.filter(d => d.status === DriverStatus.ON_LEAVE).length
    };

    const routeStats = {
      total: routes.length,
      active: routes.length // TODO: Add route status filtering when available
    };

    return { vehicleStats, driverStats, routeStats };
  }

  // Configuration methods
  updateConfig(newConfig: Partial<DataProviderConfig>): void {
    this.config = { ...this.config, ...newConfig };
    this.client = this.createAxiosInstance();
  }

  getConfig(): DataProviderConfig {
    return { ...this.config };
  }

  // Connection status
  async testConnection(): Promise<{
    isConnected: boolean;
    responseTime?: number;
    error?: string;
  }> {
    const startTime = Date.now();
    try {
      await this.healthCheck();
      return {
        isConnected: true,
        responseTime: Date.now() - startTime
      };
    } catch (error) {
      return {
        isConnected: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      };
    }
  }
}

// Export singleton instance
export const dataProvider = CentralizedDataProvider.getInstance();

// Export types for use in other modules
export type { DataProviderConfig, ApiResponse, PaginatedResponse };
