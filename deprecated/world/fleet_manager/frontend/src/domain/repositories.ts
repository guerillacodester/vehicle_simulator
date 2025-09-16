/**
 * REPOSITORY INTERFACES - Domain contracts
 * These define what our application needs, not how it's implemented
 * Following Interface Segregation Principle
 */

import { Vehicle, Driver, Route, Stop, Timetable, Assignment } from './entities';

export interface BaseRepository<T> {
  findAll(): Promise<T[]>;
  findById(id: string): Promise<T | null>;
  create(entity: Omit<T, 'id' | 'createdAt' | 'updatedAt'>): Promise<T>;
  update(id: string, entity: Partial<T>): Promise<T>;
  delete(id: string): Promise<void>;
}

export interface VehicleRepository extends BaseRepository<Vehicle> {
  findByDepotId(depotId: string): Promise<Vehicle[]>;
  findByStatus(status: string): Promise<Vehicle[]>;
  bulkCreate(vehicles: Omit<Vehicle, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<Vehicle[]>;
}

export interface DriverRepository extends BaseRepository<Driver> {
  findByStatus(status: string): Promise<Driver[]>;
  findByLicenseNumber(licenseNumber: string): Promise<Driver | null>;
  bulkCreate(drivers: Omit<Driver, 'id' | 'createdAt' | 'updatedAt'>[]): Promise<Driver[]>;
}

export interface RouteRepository extends BaseRepository<Route> {
  findByCountryId(countryId: string): Promise<Route[]>;
  findByRouteCode(routeCode: string): Promise<Route | null>;
}

export interface StopRepository extends BaseRepository<Stop> {
  findByCountryId(countryId: string): Promise<Stop[]>;
  findByCode(code: string): Promise<Stop | null>;
  findNearby(latitude: number, longitude: number, radiusKm: number): Promise<Stop[]>;
}

export interface TimetableRepository extends BaseRepository<Timetable> {
  findByRouteId(routeId: string): Promise<Timetable[]>;
  findByServiceId(serviceId: string): Promise<Timetable[]>;
  findByDateRange(from: Date, to: Date): Promise<Timetable[]>;
}

export interface AssignmentRepository extends BaseRepository<Assignment> {
  findByVehicleId(vehicleId: string): Promise<Assignment[]>;
  findByDriverId(driverId: string): Promise<Assignment[]>;
  findByDate(date: Date): Promise<Assignment[]>;
  findConflicts(vehicleId: string, driverId: string, date: Date, startTime: string, endTime: string): Promise<Assignment[]>;
}
