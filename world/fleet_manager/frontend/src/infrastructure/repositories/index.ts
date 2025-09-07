/**
 * INFRASTRUCTURE LAYER - External Dependencies Implementation
 * These implement the repository interfaces using concrete technologies
 * They depend on domain abstractions, not the other way around
 */

import { dataProvider } from '../data-provider';
import { MockApiService } from '../mock-api';
import { 
  Vehicle, 
  Driver, 
  Route, 
  Stop, 
  Timetable, 
  Assignment,
  VehicleStatus 
} from '@/domain/entities';
import { 
  VehicleRepository, 
  DriverRepository, 
  RouteRepository,
  StopRepository,
  TimetableRepository,
  AssignmentRepository 
} from '@/domain/repositories';

// Configuration for API client
interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
  enableMock?: boolean;
}

export class ApiClient {
  private mockApi: MockApiService;
  private useMock: boolean = false;
  private useRemoteAPI: boolean = true;

  constructor(config: ApiConfig) {
    this.mockApi = MockApiService.getInstance();
    this.useMock = config.enableMock || false;
    
    // Configure the data provider if not using mock
    if (!this.useMock && config.baseURL) {
      dataProvider.updateConfig({
        baseURL: config.baseURL,
        timeout: config.timeout,
        enableLogging: true
      });
    }
  }

  async get<T>(url: string): Promise<T> {
    if (this.useMock) {
      const response = await this.mockApi.get<T>(url);
      return response.data;
    }
    
    try {
      return await dataProvider.get<T>(url);
    } catch (error) {
      console.warn('Remote API failed, falling back to mock:', error);
      const response = await this.mockApi.get<T>(url);
      return response.data;
    }
  }

  async post<T>(url: string, data: unknown): Promise<T> {
    if (this.useMock) {
      const response = await this.mockApi.post<T>(url, data);
      return response.data;
    }
    
    try {
      return await dataProvider.post<T>(url, data);
    } catch (error) {
      console.warn('Remote API failed, falling back to mock:', error);
      const response = await this.mockApi.post<T>(url, data);
      return response.data;
    }
  }

  async put<T>(url: string, data: unknown): Promise<T> {
    if (this.useMock) {
      const response = await this.mockApi.put<T>(url, data);
      return response.data;
    }
    
    try {
      return await dataProvider.put<T>(url, data);
    } catch (error) {
      console.warn('Remote API failed, falling back to mock:', error);
      const response = await this.mockApi.put<T>(url, data);
      return response.data;
    }
  }

  async delete(url: string): Promise<void> {
    if (this.useMock) {
      await this.mockApi.delete(url);
      return;
    }
    
    try {
      await dataProvider.delete(url);
    } catch (error) {
      console.warn('Remote API failed, falling back to mock:', error);
      await this.mockApi.delete(url);
    }
  }

  // Health check method to test connectivity
  async healthCheck(): Promise<boolean> {
    if (this.useMock) {
      return true;
    }
    
    return await dataProvider.healthCheck();
  }
}

// Concrete Repository Implementations
export class ApiVehicleRepository implements VehicleRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Vehicle[]> {
    return this.apiClient.get<Vehicle[]>('/api/vehicles');
  }

  async findById(id: string): Promise<Vehicle | null> {
    try {
      return await this.apiClient.get<Vehicle>(`/api/vehicles/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByPlateNumber(plateNumber: string): Promise<Vehicle | null> {
    try {
      return await this.apiClient.get<Vehicle>(`/api/vehicles/plate/${plateNumber}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByStatus(status: VehicleStatus): Promise<Vehicle[]> {
    return this.apiClient.get<Vehicle[]>(`/api/vehicles?status=${status}`);
  }

  async findByDepot(depotId: string): Promise<Vehicle[]> {
    return this.apiClient.get<Vehicle[]>(`/api/vehicles?depotId=${depotId}`);
  }

  async findByDepotId(depotId: string): Promise<Vehicle[]> {
    return this.findByDepot(depotId);
  }

  async bulkCreate(vehicles: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<Vehicle[]> {
    return this.apiClient.post<Vehicle[]>('/api/vehicles/bulk', { vehicles });
  }

  async create(data: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>): Promise<Vehicle> {
    return this.apiClient.post<Vehicle>('/api/vehicles', data);
  }

  async update(id: string, data: Partial<Vehicle>): Promise<Vehicle> {
    return this.apiClient.put<Vehicle>(`/api/vehicles/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/vehicles/${id}`);
  }
}

export class ApiDriverRepository implements DriverRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Driver[]> {
    return this.apiClient.get<Driver[]>('/api/drivers');
  }

  async findById(id: string): Promise<Driver | null> {
    try {
      return await this.apiClient.get<Driver>(`/api/drivers/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByEmployeeId(employeeId: string): Promise<Driver | null> {
    try {
      return await this.apiClient.get<Driver>(`/api/drivers/employee/${employeeId}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByLicenseNumber(licenseNumber: string): Promise<Driver | null> {
    try {
      return await this.apiClient.get<Driver>(`/api/drivers/license/${licenseNumber}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByStatus(status: string): Promise<Driver[]> {
    return this.apiClient.get<Driver[]>(`/api/drivers?status=${status}`);
  }

  async bulkCreate(drivers: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<Driver[]> {
    return this.apiClient.post<Driver[]>('/api/drivers/bulk', { drivers });
  }

  async create(data: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>): Promise<Driver> {
    return this.apiClient.post<Driver>('/api/drivers', data);
  }

  async update(id: string, data: Partial<Driver>): Promise<Driver> {
    return this.apiClient.put<Driver>(`/api/drivers/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/drivers/${id}`);
  }
}

export class ApiRouteRepository implements RouteRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Route[]> {
    return this.apiClient.get<Route[]>('/api/routes');
  }

  async findById(id: string): Promise<Route | null> {
    try {
      return await this.apiClient.get<Route>(`/api/routes/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByRouteNumber(routeNumber: string): Promise<Route | null> {
    try {
      return await this.apiClient.get<Route>(`/api/routes/number/${routeNumber}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByCountryId(countryId: string): Promise<Route[]> {
    return this.apiClient.get<Route[]>(`/api/routes?countryId=${countryId}`);
  }

  async findByRouteCode(routeCode: string): Promise<Route | null> {
    try {
      return await this.apiClient.get<Route>(`/api/routes/code/${routeCode}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async create(data: Omit<Route, 'id' | 'createdAt' | 'updatedAt'>): Promise<Route> {
    return this.apiClient.post<Route>('/api/routes', data);
  }

  async update(id: string, data: Partial<Route>): Promise<Route> {
    return this.apiClient.put<Route>(`/api/routes/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/routes/${id}`);
  }
}

// Additional repositories would follow similar patterns...
export class ApiStopRepository implements StopRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>('/api/stops');
  }

  async findById(id: string): Promise<Stop | null> {
    try {
      return await this.apiClient.get<Stop>(`/api/stops/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByRoute(routeId: string): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>(`/api/stops/route/${routeId}`);
  }

  async findByCountryId(countryId: string): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>(`/api/stops?countryId=${countryId}`);
  }

  async findByCode(code: string): Promise<Stop | null> {
    try {
      return await this.apiClient.get<Stop>(`/api/stops/code/${code}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findNearby(latitude: number, longitude: number, radiusKm: number): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>(`/api/stops/nearby?lat=${latitude}&lon=${longitude}&radius=${radiusKm}`);
  }

  async create(data: Omit<Stop, 'id' | 'createdAt' | 'updatedAt'>): Promise<Stop> {
    return this.apiClient.post<Stop>('/api/stops', data);
  }

  async update(id: string, data: Partial<Stop>): Promise<Stop> {
    return this.apiClient.put<Stop>(`/api/stops/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/stops/${id}`);
  }
}

// Dependency Injection Container
export class DependencyContainer {
  private apiClient: ApiClient;
  private vehicleRepository: VehicleRepository;
  private driverRepository: DriverRepository;
  private routeRepository: RouteRepository;
  private stopRepository: StopRepository;

  constructor(apiConfig: ApiConfig) {
    // Initialize infrastructure
    this.apiClient = new ApiClient(apiConfig);
    
    // Initialize repositories
    this.vehicleRepository = new ApiVehicleRepository(this.apiClient);
    this.driverRepository = new ApiDriverRepository(this.apiClient);
    this.routeRepository = new ApiRouteRepository(this.apiClient);
    this.stopRepository = new ApiStopRepository(this.apiClient);
  }

  getVehicleRepository(): VehicleRepository {
    return this.vehicleRepository;
  }

  getDriverRepository(): DriverRepository {
    return this.driverRepository;
  }

  getRouteRepository(): RouteRepository {
    return this.routeRepository;
  }

  getStopRepository(): StopRepository {
    return this.stopRepository;
  }
}
