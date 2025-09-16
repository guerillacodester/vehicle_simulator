/**
 * DOMAIN ENTITIES - Core business objects
 * These represent the fundamental business concepts
 * NO dependencies on external frameworks or libraries
 */

export interface Entity {
  readonly id: string;
  readonly createdAt: Date;
  readonly updatedAt?: Date;
}

export interface Vehicle extends Entity {
  readonly countryId: string;
  readonly depotId: string;
  readonly plateNumber: string;
  readonly regCode: string;
  readonly model: string;
  readonly capacity: number;
  readonly status?: VehicleStatus;
}

export enum VehicleStatus {
  ACTIVE = 'ACTIVE',
  MAINTENANCE = 'MAINTENANCE',
  OUT_OF_SERVICE = 'OUT_OF_SERVICE'
}

export interface Driver extends Entity {
  readonly countryId: string;
  readonly employeeId: string;
  readonly firstName: string;
  readonly lastName: string;
  readonly licenseNumber: string;
  readonly phoneNumber?: string;
  readonly email?: string;
  readonly status?: DriverStatus;
}

export enum DriverStatus {
  ACTIVE = 'ACTIVE',
  ON_LEAVE = 'ON_LEAVE',
  SUSPENDED = 'SUSPENDED',
  TERMINATED = 'TERMINATED'
}

export interface Route extends Entity {
  readonly countryId: string;
  readonly routeCode: string;
  readonly name: string;
  readonly description?: string;
  readonly geojson?: Record<string, unknown>; // TODO: Replace with proper GeoJSON type when @types/geojson is added
  readonly distance?: number;
  readonly estimatedDuration?: number;
}

export interface Stop extends Entity {
  readonly countryId: string;
  readonly code: string;
  readonly name: string;
  readonly latitude: number;
  readonly longitude: number;
  readonly zoneId?: string;
}

export interface Timetable extends Entity {
  readonly routeId: string;
  readonly serviceId: string;
  readonly name: string;
  readonly validFrom: Date;
  readonly validTo: Date;
  readonly schedule: TimetableEntry[];
}

export interface TimetableEntry {
  readonly stopId: string;
  readonly arrivalTime: string; // HH:MM format
  readonly departureTime: string; // HH:MM format
  readonly sequence: number;
}

export interface Assignment extends Entity {
  readonly vehicleId: string;
  readonly driverId: string;
  readonly timetableId: string;
  readonly assignedDate: Date;
  readonly startTime: string;
  readonly endTime: string;
  readonly status: AssignmentStatus;
}

export enum AssignmentStatus {
  SCHEDULED = 'SCHEDULED',
  ACTIVE = 'ACTIVE',
  COMPLETED = 'COMPLETED',
  CANCELLED = 'CANCELLED'
}
