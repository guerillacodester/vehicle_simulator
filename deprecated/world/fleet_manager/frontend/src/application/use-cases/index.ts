/**
 * USE CASES - Application Business Logic
 * These orchestrate domain services and repositories
 * Each use case represents a single user action/workflow
 */

import { Vehicle, Driver, VehicleStatus } from '@/domain/entities';
import { VehicleRepository, DriverRepository } from '@/domain/repositories';
import { VehicleAssignmentService, DriverAssignmentService, FileValidationService } from '@/domain/services';

// Type for CSV data row
interface VehicleCsvRow {
  [key: string]: string | undefined;
  countryId: string;
  depotId: string;
  plateNumber: string;
  regCode: string;
  model: string;
  capacity: string; // CSV values come as strings
  status?: string;
}

export class VehicleUseCases {
  constructor(
    private vehicleRepository: VehicleRepository,
    private vehicleService: VehicleAssignmentService,
    private fileValidationService: FileValidationService
  ) {}

  async getAllVehicles(): Promise<Vehicle[]> {
    return this.vehicleRepository.findAll();
  }

  async getVehicleById(id: string): Promise<Vehicle | null> {
    return this.vehicleRepository.findById(id);
  }

  async createVehicle(data: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>): Promise<Vehicle> {
    // Business validation
    if (!data.plateNumber || data.plateNumber.trim() === '') {
      throw new Error('Plate number is required');
    }

    if (data.capacity <= 0) {
      throw new Error('Capacity must be greater than 0');
    }

    return this.vehicleRepository.create(data);
  }

  async updateVehicle(id: string, data: Partial<Vehicle>): Promise<Vehicle> {
    const existing = await this.vehicleRepository.findById(id);
    if (!existing) {
      throw new Error('Vehicle not found');
    }

    return this.vehicleRepository.update(id, data);
  }

  async deleteVehicle(id: string): Promise<void> {
    const existing = await this.vehicleRepository.findById(id);
    if (!existing) {
      throw new Error('Vehicle not found');
    }

    return this.vehicleRepository.delete(id);
  }

  async bulkCreateVehicles(csvData: VehicleCsvRow[]): Promise<{ 
    successful: Vehicle[]; 
    failed: Array<{ row: number; error: string }> 
  }> {
    const validation = this.fileValidationService.validateVehicleCSV(csvData);
    if (!validation.isValid) {
      throw new Error(`CSV validation failed: ${validation.errors.join(', ')}`);
    }

    const successful: Vehicle[] = [];
    const failed: Array<{ row: number; error: string }> = [];

    for (let i = 0; i < csvData.length; i++) {
      try {
        const vehicle = await this.createVehicle({
          countryId: csvData[i].countryId,
          depotId: csvData[i].depotId,
          plateNumber: csvData[i].plateNumber,
          regCode: csvData[i].regCode,
          model: csvData[i].model,
          capacity: parseInt(csvData[i].capacity),
          status: (csvData[i].status as VehicleStatus) || ('ACTIVE' as VehicleStatus)
        });
        successful.push(vehicle);
      } catch (error) {
        failed.push({ 
          row: i + 1, 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
      }
    }

    return { successful, failed };
  }
}

export class DriverUseCases {
  constructor(
    private driverRepository: DriverRepository,
    private driverService: DriverAssignmentService
  ) {}

  async getAllDrivers(): Promise<Driver[]> {
    return this.driverRepository.findAll();
  }

  async getDriverById(id: string): Promise<Driver | null> {
    return this.driverRepository.findById(id);
  }

  async createDriver(data: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>): Promise<Driver> {
    // Business validation
    if (!data.employeeId || data.employeeId.trim() === '') {
      throw new Error('Employee ID is required');
    }

    if (!data.licenseNumber || data.licenseNumber.trim() === '') {
      throw new Error('License number is required');
    }

    // Check for duplicate license
    const existingDriver = await this.driverRepository.findByLicenseNumber(data.licenseNumber);
    if (existingDriver) {
      throw new Error('A driver with this license number already exists');
    }

    return this.driverRepository.create(data);
  }

  async updateDriver(id: string, data: Partial<Driver>): Promise<Driver> {
    const existing = await this.driverRepository.findById(id);
    if (!existing) {
      throw new Error('Driver not found');
    }

    return this.driverRepository.update(id, data);
  }

  async deleteDriver(id: string): Promise<void> {
    const existing = await this.driverRepository.findById(id);
    if (!existing) {
      throw new Error('Driver not found');
    }

    return this.driverRepository.delete(id);
  }
}
