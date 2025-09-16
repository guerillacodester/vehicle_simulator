/**
 * MOCK API SERVICE - Development Only
 * This provides mock data for development when the real API is not available
 */

import { Vehicle, Driver, Route, Stop, VehicleStatus, DriverStatus } from '@/domain/entities';

// Mock data
const mockVehicles: Vehicle[] = [
  {
    id: '1',
    countryId: 'BB',
    depotId: 'depot-001',
    plateNumber: 'BBX-1234',
    regCode: 'REG001',
    model: 'Mercedes Sprinter',
    capacity: 16,
    status: VehicleStatus.ACTIVE,
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-15')
  },
  {
    id: '2',
    countryId: 'BB',
    depotId: 'depot-001',
    plateNumber: 'BBX-5678',
    regCode: 'REG002',
    model: 'Toyota Hiace',
    capacity: 14,
    status: VehicleStatus.ACTIVE,
    createdAt: new Date('2024-01-16'),
    updatedAt: new Date('2024-01-16')
  },
  {
    id: '3',
    countryId: 'BB',
    depotId: 'depot-002',
    plateNumber: 'BBX-9012',
    regCode: 'REG003',
    model: 'Ford Transit',
    capacity: 12,
    status: VehicleStatus.MAINTENANCE,
    createdAt: new Date('2024-01-17'),
    updatedAt: new Date('2024-01-17')
  }
];

const mockDrivers: Driver[] = [
  {
    id: '1',
    countryId: 'BB',
    employeeId: 'EMP001',
    firstName: 'John',
    lastName: 'Smith',
    licenseNumber: 'LIC001',
    phoneNumber: '+1-246-555-0123',
    email: 'john.smith@email.com',
    status: DriverStatus.ACTIVE,
    createdAt: new Date('2024-01-15'),
    updatedAt: new Date('2024-01-15')
  },
  {
    id: '2',
    countryId: 'BB',
    employeeId: 'EMP002',
    firstName: 'Jane',
    lastName: 'Doe',
    licenseNumber: 'LIC002',
    phoneNumber: '+1-246-555-0124',
    email: 'jane.doe@email.com',
    status: DriverStatus.ACTIVE,
    createdAt: new Date('2024-01-16'),
    updatedAt: new Date('2024-01-16')
  }
];

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export class MockApiService {
  private static instance: MockApiService;
  private isEnabled: boolean = true;

  static getInstance(): MockApiService {
    if (!MockApiService.instance) {
      MockApiService.instance = new MockApiService();
    }
    return MockApiService.instance;
  }

  setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
  }

  async get<T>(url: string): Promise<{ data: T }> {
    if (!this.isEnabled) {
      throw new Error('Mock API is disabled');
    }

    await delay(200); // Simulate network delay

    // Route the mock requests
    if (url.includes('/api/vehicles')) {
      if (url.includes('/api/vehicles/') && !url.includes('?')) {
        // Get single vehicle by ID
        const id = url.split('/').pop();
        const vehicle = mockVehicles.find(v => v.id === id);
        if (!vehicle) {
          throw new Error('Vehicle not found');
        }
        return { data: vehicle as T };
      }
      // Get all vehicles or filtered vehicles
      return { data: mockVehicles as T };
    }

    if (url.includes('/api/drivers')) {
      if (url.includes('/api/drivers/') && !url.includes('?')) {
        // Get single driver by ID
        const id = url.split('/').pop();
        const driver = mockDrivers.find(d => d.id === id);
        if (!driver) {
          throw new Error('Driver not found');
        }
        return { data: driver as T };
      }
      // Get all drivers
      return { data: mockDrivers as T };
    }

    if (url.includes('/api/routes')) {
      return { data: [] as T }; // No mock routes yet
    }

    if (url.includes('/api/stops')) {
      return { data: [] as T }; // No mock stops yet
    }

    throw new Error(`Mock API: Unhandled route ${url}`);
  }

  async post<T>(url: string, data: unknown): Promise<{ data: T }> {
    if (!this.isEnabled) {
      throw new Error('Mock API is disabled');
    }

    await delay(300); // Simulate network delay

    if (url.includes('/api/vehicles')) {
      const newVehicle: Vehicle = {
        id: (mockVehicles.length + 1).toString(),
        ...(data as Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>),
        createdAt: new Date(),
        updatedAt: new Date()
      };
      mockVehicles.push(newVehicle);
      return { data: newVehicle as T };
    }

    if (url.includes('/api/drivers')) {
      const newDriver: Driver = {
        id: (mockDrivers.length + 1).toString(),
        ...(data as Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>),
        createdAt: new Date(),
        updatedAt: new Date()
      };
      mockDrivers.push(newDriver);
      return { data: newDriver as T };
    }

    throw new Error(`Mock API: Unhandled POST route ${url}`);
  }

  async put<T>(url: string, data: unknown): Promise<{ data: T }> {
    if (!this.isEnabled) {
      throw new Error('Mock API is disabled');
    }

    await delay(250); // Simulate network delay

    if (url.includes('/api/vehicles/')) {
      const id = url.split('/').pop();
      const vehicleIndex = mockVehicles.findIndex(v => v.id === id);
      if (vehicleIndex === -1) {
        throw new Error('Vehicle not found');
      }
      mockVehicles[vehicleIndex] = {
        ...mockVehicles[vehicleIndex],
        ...(data as Partial<Vehicle>),
        updatedAt: new Date()
      };
      return { data: mockVehicles[vehicleIndex] as T };
    }

    if (url.includes('/api/drivers/')) {
      const id = url.split('/').pop();
      const driverIndex = mockDrivers.findIndex(d => d.id === id);
      if (driverIndex === -1) {
        throw new Error('Driver not found');
      }
      mockDrivers[driverIndex] = {
        ...mockDrivers[driverIndex],
        ...(data as Partial<Driver>),
        updatedAt: new Date()
      };
      return { data: mockDrivers[driverIndex] as T };
    }

    throw new Error(`Mock API: Unhandled PUT route ${url}`);
  }

  async delete(url: string): Promise<{ data: void }> {
    if (!this.isEnabled) {
      throw new Error('Mock API is disabled');
    }

    await delay(200); // Simulate network delay

    if (url.includes('/api/vehicles/')) {
      const id = url.split('/').pop();
      const vehicleIndex = mockVehicles.findIndex(v => v.id === id);
      if (vehicleIndex === -1) {
        throw new Error('Vehicle not found');
      }
      mockVehicles.splice(vehicleIndex, 1);
      return { data: void 0 };
    }

    if (url.includes('/api/drivers/')) {
      const id = url.split('/').pop();
      const driverIndex = mockDrivers.findIndex(d => d.id === id);
      if (driverIndex === -1) {
        throw new Error('Driver not found');
      }
      mockDrivers.splice(driverIndex, 1);
      return { data: void 0 };
    }

    throw new Error(`Mock API: Unhandled DELETE route ${url}`);
  }
}
