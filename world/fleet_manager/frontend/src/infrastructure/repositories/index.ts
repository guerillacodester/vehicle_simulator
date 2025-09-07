/**
 * INFRASTRUCTURE LAYER - External Dependencies Implementation
 * These implement the repository interfaces using concrete technologies
 * They depend on domain abstractions, not the other way around
 */

import { dataProvider } from '../data-provider';
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

// API Response Types (what the API actually returns)
interface ApiVehicleResponse {
  vehicle_id: string;
  country_id: string;
  reg_code: string;
  home_depot_id: string | null;
  preferred_route_id: string | null;
  status: 'available' | 'in_service' | 'maintenance' | 'retired';
  profile_id: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface ApiDriverResponse {
  driver_id: string;
  country_id: string;
  name: string;
  license_no: string;
  home_depot_id: string | null;
  employment_status: string;
  created_at: string;
  updated_at: string;
}

// Mapping functions to transform API responses to domain entities
function mapApiVehicleToVehicle(apiVehicle: ApiVehicleResponse): Vehicle {
  const statusMap: Record<string, VehicleStatus> = {
    'available': VehicleStatus.ACTIVE,
    'in_service': VehicleStatus.ACTIVE,
    'maintenance': VehicleStatus.MAINTENANCE,
    'retired': VehicleStatus.OUT_OF_SERVICE
  };

  return {
    id: apiVehicle.vehicle_id,
    countryId: apiVehicle.country_id,
    depotId: apiVehicle.home_depot_id || '',
    plateNumber: apiVehicle.reg_code, // Using reg_code as plateNumber for now
    regCode: apiVehicle.reg_code,
    model: 'Unknown', // API doesn't provide model yet
    capacity: 0, // API doesn't provide capacity yet
    status: statusMap[apiVehicle.status] || VehicleStatus.ACTIVE,
    createdAt: new Date(apiVehicle.created_at),
    updatedAt: apiVehicle.updated_at ? new Date(apiVehicle.updated_at) : undefined
  };
}

function mapApiDriverToDriver(apiDriver: ApiDriverResponse): Driver {
  const [firstName, ...lastNameParts] = apiDriver.name.split(' ');
  const lastName = lastNameParts.join(' ');

  return {
    id: apiDriver.driver_id,
    countryId: apiDriver.country_id,
    employeeId: apiDriver.driver_id, // Use driver_id as employeeId since employee_id is not in the API
    firstName: firstName || '',
    lastName: lastName || '',
    licenseNumber: apiDriver.license_no,
    phoneNumber: undefined, // Not available in current API response
    email: undefined, // Not available in current API response
    createdAt: new Date(apiDriver.created_at),
    updatedAt: apiDriver.updated_at ? new Date(apiDriver.updated_at) : undefined
  };
}

// Configuration for API client
interface ApiConfig {
  baseURL: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export class ApiClient {
  constructor(config: ApiConfig) {
    // Configure the data provider to use real API only
    dataProvider.updateConfig({
      baseURL: config.baseURL,
      timeout: config.timeout || 10000,
      enableLogging: true
    });
  }

  async get<T>(url: string): Promise<T> {
    return dataProvider.get<T>(url);
  }

  async post<T>(url: string, data: unknown): Promise<T> {
    return dataProvider.post<T>(url, data);
  }

  async put<T>(url: string, data: unknown): Promise<T> {
    return dataProvider.put<T>(url, data);
  }

  async patch<T>(url: string, data: unknown): Promise<T> {
    return dataProvider.patch<T>(url, data);
  }

  async delete(url: string): Promise<void> {
    return dataProvider.delete(url);
  }

  // Health check method to test connectivity
  async healthCheck(): Promise<boolean> {
    return dataProvider.healthCheck();
  }
}

// Concrete Repository Implementations
export class ApiVehicleRepository implements VehicleRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Vehicle[]> {
    const apiVehicles = await this.apiClient.get<ApiVehicleResponse[]>('/api/v1/vehicles');
    return apiVehicles.map(mapApiVehicleToVehicle);
  }

  async findById(id: string): Promise<Vehicle | null> {
    try {
      const apiVehicle = await this.apiClient.get<ApiVehicleResponse>(`/api/v1/vehicles/${id}`);
      return mapApiVehicleToVehicle(apiVehicle);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByPlateNumber(plateNumber: string): Promise<Vehicle | null> {
    try {
      const apiVehicle = await this.apiClient.get<ApiVehicleResponse>(`/api/v1/vehicles/plate/${plateNumber}`);
      return mapApiVehicleToVehicle(apiVehicle);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByStatus(status: VehicleStatus): Promise<Vehicle[]> {
    // Map domain status to API status
    const apiStatusMap: Record<VehicleStatus, string> = {
      [VehicleStatus.ACTIVE]: 'available',
      [VehicleStatus.MAINTENANCE]: 'maintenance',
      [VehicleStatus.OUT_OF_SERVICE]: 'retired'
    };
    
    const apiVehicles = await this.apiClient.get<ApiVehicleResponse[]>(`/api/v1/vehicles?status=${apiStatusMap[status]}`);
    return apiVehicles.map(mapApiVehicleToVehicle);
  }

  async findByDepot(depotId: string): Promise<Vehicle[]> {
    const apiVehicles = await this.apiClient.get<ApiVehicleResponse[]>(`/api/v1/vehicles?depotId=${depotId}`);
    return apiVehicles.map(mapApiVehicleToVehicle);
  }

  async findByDepotId(depotId: string): Promise<Vehicle[]> {
    return this.findByDepot(depotId);
  }

  async bulkCreate(vehicles: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<Vehicle[]> {
    // This would need proper mapping from domain to API format
    const apiVehicles = await this.apiClient.post<ApiVehicleResponse[]>('/api/v1/vehicles/bulk', { vehicles });
    return apiVehicles.map(mapApiVehicleToVehicle);
  }

  async create(data: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>): Promise<Vehicle> {
    // Map domain vehicle to API format
    const apiData = {
      country_id: data.countryId,
      reg_code: data.regCode,
      status: 'available' // Default status
    };
    
    const apiVehicle = await this.apiClient.post<ApiVehicleResponse>('/api/v1/vehicles', apiData);
    return mapApiVehicleToVehicle(apiVehicle);
  }

  async update(id: string, data: Partial<Vehicle>): Promise<Vehicle> {
    // This would need proper mapping from domain to API format
    const apiVehicle = await this.apiClient.put<ApiVehicleResponse>(`/api/v1/vehicles/${id}`, data);
    return mapApiVehicleToVehicle(apiVehicle);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/v1/vehicles/${id}`);
  }
}

export class ApiDriverRepository implements DriverRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Driver[]> {
    const apiDrivers = await this.apiClient.get<ApiDriverResponse[]>('/api/v1/drivers');
    return apiDrivers.map(mapApiDriverToDriver);
  }

  async findById(id: string): Promise<Driver | null> {
    try {
      const apiDriver = await this.apiClient.get<ApiDriverResponse>(`/api/v1/drivers/${id}`);
      return mapApiDriverToDriver(apiDriver);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByEmployeeId(employeeId: string): Promise<Driver | null> {
    try {
      const apiDriver = await this.apiClient.get<ApiDriverResponse>(`/api/v1/drivers/employee/${employeeId}`);
      return mapApiDriverToDriver(apiDriver);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByLicenseNumber(licenseNumber: string): Promise<Driver | null> {
    try {
      const apiDriver = await this.apiClient.get<ApiDriverResponse>(`/api/v1/drivers/license/${licenseNumber}`);
      return mapApiDriverToDriver(apiDriver);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByStatus(status: string): Promise<Driver[]> {
    const apiDrivers = await this.apiClient.get<ApiDriverResponse[]>(`/api/v1/drivers?status=${status}`);
    return apiDrivers.map(mapApiDriverToDriver);
  }

  async bulkCreate(drivers: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<Driver[]> {
    // This would need proper mapping from domain to API format
    const apiDrivers = await this.apiClient.post<ApiDriverResponse[]>('/api/v1/drivers/bulk', { drivers });
    return apiDrivers.map(mapApiDriverToDriver);
  }

  async create(data: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>): Promise<Driver> {
    // Map domain driver to API format
    const apiData = {
      country_id: data.countryId,
      employee_id: data.employeeId,
      name: `${data.firstName} ${data.lastName}`.trim(),
      license_no: data.licenseNumber,
      phone_number: data.phoneNumber || null,
      email: data.email || null
    };
    
    const apiDriver = await this.apiClient.post<ApiDriverResponse>('/api/v1/drivers', apiData);
    return mapApiDriverToDriver(apiDriver);
  }

  async update(id: string, data: Partial<Driver>): Promise<Driver> {
    // This would need proper mapping from domain to API format
    const apiDriver = await this.apiClient.put<ApiDriverResponse>(`/api/v1/drivers/${id}`, data);
    return mapApiDriverToDriver(apiDriver);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/v1/drivers/${id}`);
  }
}

export class ApiRouteRepository implements RouteRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Route[]> {
    return this.apiClient.get<Route[]>('/api/v1/routes');
  }

  async findById(id: string): Promise<Route | null> {
    try {
      return await this.apiClient.get<Route>(`/api/v1/routes/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByRouteNumber(routeNumber: string): Promise<Route | null> {
    try {
      return await this.apiClient.get<Route>(`/api/v1/routes/number/${routeNumber}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByCountryId(countryId: string): Promise<Route[]> {
    return this.apiClient.get<Route[]>(`/api/v1/routes?countryId=${countryId}`);
  }

  async findByRouteCode(routeCode: string): Promise<Route | null> {
    try {
      return await this.apiClient.get<Route>(`/api/v1/routes/code/${routeCode}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async create(data: Omit<Route, 'id' | 'createdAt' | 'updatedAt'>): Promise<Route> {
    return this.apiClient.post<Route>('/api/v1/routes', data);
  }

  async update(id: string, data: Partial<Route>): Promise<Route> {
    return this.apiClient.put<Route>(`/api/v1/routes/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/v1/routes/${id}`);
  }
}

// Additional repositories would follow similar patterns...
export class ApiStopRepository implements StopRepository {
  constructor(private apiClient: ApiClient) {}

  async findAll(): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>('/api/v1/stops');
  }

  async findById(id: string): Promise<Stop | null> {
    try {
      return await this.apiClient.get<Stop>(`/api/v1/stops/${id}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findByRoute(routeId: string): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>(`/api/v1/stops/route/${routeId}`);
  }

  async findByCountryId(countryId: string): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>(`/api/v1/stops?countryId=${countryId}`);
  }

  async findByCode(code: string): Promise<Stop | null> {
    try {
      return await this.apiClient.get<Stop>(`/api/v1/stops/code/${code}`);
    } catch (error) {
      if (error instanceof Error && error.message === 'Resource not found') {
        return null;
      }
      throw error;
    }
  }

  async findNearby(latitude: number, longitude: number, radiusKm: number): Promise<Stop[]> {
    return this.apiClient.get<Stop[]>(`/api/v1/stops/nearby?lat=${latitude}&lon=${longitude}&radius=${radiusKm}`);
  }

  async create(data: Omit<Stop, 'id' | 'createdAt' | 'updatedAt'>): Promise<Stop> {
    return this.apiClient.post<Stop>('/api/v1/stops', data);
  }

  async update(id: string, data: Partial<Stop>): Promise<Stop> {
    return this.apiClient.put<Stop>(`/api/v1/stops/${id}`, data);
  }

  async delete(id: string): Promise<void> {
    return this.apiClient.delete(`/api/v1/stops/${id}`);
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
