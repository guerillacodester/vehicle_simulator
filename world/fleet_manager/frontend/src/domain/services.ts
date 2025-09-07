/**
 * DOMAIN SERVICES - Business Logic
 * These contain domain rules and business logic
 * Single Responsibility: Each service handles one business concern
 */

import { Vehicle, Driver, Assignment, AssignmentStatus } from './entities';

// Type for raw CSV data (before validation)
interface CsvRowData {
  [key: string]: string | undefined;
}

// Type for GeoJSON-like data structure
interface GeoJSONLike {
  type?: string;
  features?: unknown[];
  coordinates?: unknown[];
  geometry?: unknown;
  properties?: Record<string, unknown>;
}

export class VehicleAssignmentService {
  /**
   * Business rule: Check if a vehicle can be assigned
   */
  canAssignVehicle(vehicle: Vehicle): boolean {
    return vehicle.status === 'ACTIVE';
  }

  /**
   * Business rule: Validate vehicle capacity for route
   */
  isVehicleSuitableForRoute(vehicle: Vehicle, requiredCapacity: number): boolean {
    return vehicle.capacity >= requiredCapacity;
  }
}

export class DriverAssignmentService {
  /**
   * Business rule: Check if a driver can be assigned
   */
  canAssignDriver(driver: Driver): boolean {
    return driver.status === 'ACTIVE';
  }

  /**
   * Business rule: Check if driver has valid license
   */
  hasValidLicense(driver: Driver): boolean {
    return !!driver.licenseNumber && driver.licenseNumber.trim().length > 0;
  }
}

export class SchedulingService {
  /**
   * Business rule: Check for scheduling conflicts
   */
  hasConflict(
    existingAssignments: Assignment[],
    newStartTime: string,
    newEndTime: string,
    date: Date
  ): boolean {
    const newStart = this.parseTime(newStartTime);
    const newEnd = this.parseTime(newEndTime);

    return existingAssignments.some(assignment => {
      if (assignment.status === AssignmentStatus.CANCELLED) {
        return false;
      }

      const existingStart = this.parseTime(assignment.startTime);
      const existingEnd = this.parseTime(assignment.endTime);

      // Check for time overlap
      return (newStart < existingEnd && newEnd > existingStart);
    });
  }

  /**
   * Business rule: Validate assignment time bounds
   */
  isValidTimeRange(startTime: string, endTime: string): boolean {
    const start = this.parseTime(startTime);
    const end = this.parseTime(endTime);
    
    return start < end && start >= 0 && end <= 24 * 60; // Within 24 hours
  }

  private parseTime(timeString: string): number {
    const [hours, minutes] = timeString.split(':').map(Number);
    return hours * 60 + minutes;
  }
}

export class FileValidationService {
  /**
   * Business rule: Validate CSV structure for bulk upload
   */
  validateVehicleCSV(data: CsvRowData[]): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];
    const requiredFields = ['plateNumber', 'regCode', 'model', 'capacity'];

    if (!Array.isArray(data) || data.length === 0) {
      errors.push('File must contain at least one row of data');
      return { isValid: false, errors };
    }

    data.forEach((row, index) => {
      requiredFields.forEach(field => {
        if (!row[field] || row[field]?.toString().trim() === '') {
          errors.push(`Row ${index + 1}: Missing required field '${field}'`);
        }
      });

      if (row.capacity && (isNaN(Number(row.capacity)) || Number(row.capacity) <= 0)) {
        errors.push(`Row ${index + 1}: Capacity must be a positive number`);
      }
    });

    return { isValid: errors.length === 0, errors };
  }

  /**
   * Business rule: Validate GeoJSON structure
   */
  validateGeoJSON(data: GeoJSONLike): { isValid: boolean; errors: string[] } {
    const errors: string[] = [];

    if (!data || typeof data !== 'object') {
      errors.push('Invalid GeoJSON format');
      return { isValid: false, errors };
    }

    if (data.type !== 'FeatureCollection' && data.type !== 'Feature') {
      errors.push('GeoJSON must be a FeatureCollection or Feature');
    }

    if (data.type === 'FeatureCollection' && !Array.isArray(data.features)) {
      errors.push('FeatureCollection must have a features array');
    }

    return { isValid: errors.length === 0, errors };
  }
}
