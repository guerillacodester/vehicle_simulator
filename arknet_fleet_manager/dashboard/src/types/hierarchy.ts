/**
 * Hierarchical Dashboard Structure
 * 
 * Country Dashboard
 *   └─ Depots Overview (KPIs, status cards, depot list)
 *      └─ Depot Dashboard
 *         ├─ Routes Dashboard
 *         │  └─ Route Detail Dashboard
 *         ├─ Vehicles Dashboard
 *         │  └─ Vehicle Detail Dashboard
 *         └─ Drivers Dashboard
 *            └─ Driver Detail Dashboard
 */

// Navigation structure types
export interface BreadcrumbItem {
  label: string;
  level: 'country' | 'depot' | 'route' | 'vehicle' | 'driver';
  id?: string;
  icon: string;
  onClick: () => void;
}

export interface NavigationState {
  currentLevel: 'country' | 'depot' | 'route' | 'vehicle' | 'driver';
  countryId?: string;
  countryName?: string;
  depotId?: string;
  depotName?: string;
  routeId?: string;
  routeName?: string;
  vehicleId?: string;
  vehicleReg?: string;
  driverId?: string;
  driverName?: string;
  breadcrumbs: BreadcrumbItem[];
}

export interface CountryDashboardData {
  id: string;
  name: string;
  totalDepots: number;
  activeVehicles: number;
  totalRoutes: number;
  totalDrivers: number;
  overallUtilization: number;
  avgDeliveryTime: string;
  depots: DepotSummary[];
  kpis: {
    onTimeDeliveries: number;
    fuelEfficiency: number;
    driverSafety: number;
    vehicleAvailability: number;
  };
}

export interface DepotSummary {
  id: string;
  name: string;
  location: string;
  activeVehicles: number;
  totalVehicles: number;
  routes: number;
  drivers: number;
  utilization: number;
  status: 'operational' | 'maintenance' | 'closed';
}

export interface DepotDashboardData {
  id: string;
  name: string;
  location: string;
  manager: string;
  contactPhone: string;
  
  // Summary Stats
  summary: {
    totalVehicles: number;
    activeVehicles: number;
    totalRoutes: number;
    activeRoutes: number;
    totalDrivers: number;
    availableDrivers: number;
    utilization: number;
    avgDeliveryTime: string;
  };

  // Sub-resources
  routes: RouteSummary[];
  vehicles: VehicleSummary[];
  drivers: DriverSummary[];

  // KPIs
  kpis: {
    onTimeDeliveryRate: number;
    fuelConsumption: number;
    driverSafetyScore: number;
    vehicleAvailability: number;
  };

  // Alerts
  alerts: {
    critical: number;
    warning: number;
    info: number;
  };
}

export interface RouteSummary {
  id: string;
  name: string;
  routeNumber: string;
  startPoint: string;
  endPoint: string;
  distance: number;
  estimatedTime: string;
  assignedVehicles: number;
  activeVehicles: number;
  status: 'active' | 'inactive' | 'paused';
  efficiency: number;
}

export interface VehicleSummary {
  id: string;
  registration: string;
  type: string;
  status: 'active' | 'idle' | 'maintenance' | 'offline';
  location: string;
  currentRoute?: string;
  driver?: string;
  fuelLevel: number;
  utilization: number;
  lastUpdate: string;
}

export interface DriverSummary {
  id: string;
  name: string;
  licenseNumber: string;
  status: 'active' | 'idle' | 'offline';
  assignedVehicle?: string;
  currentRoute?: string;
  safetyScore: number;
  completedDeliveries: number;
  avgDeliveryTime: string;
}

// Drill-down Detail Views
export interface RouteDetailData extends RouteSummary {
  waypoints: Waypoint[];
  assignedVehicles: VehicleRouteAssignment[];
  schedule: Schedule[];
  deliveries: Delivery[];
  incidents?: Incident[];
  performance: {
    avgSpeed: number;
    avgFuelConsumption: number;
    onTimeRate: number;
    completionRate: number;
  };
}

export interface Waypoint {
  id: string;
  name: string;
  lat: number;
  lon: number;
  sequence: number;
  arrivalTime?: string;
  departureTime?: string;
}

export interface VehicleRouteAssignment {
  vehicleId: string;
  registration: string;
  driverId: string;
  driverName: string;
  startTime: string;
  endTime: string;
  status: string;
}

export interface Schedule {
  date: string;
  vehicleId: string;
  driverId: string;
  estimatedStart: string;
  estimatedEnd: string;
}

export interface Delivery {
  id: string;
  destination: string;
  status: 'completed' | 'in-progress' | 'pending';
  deliveryTime: string;
  onTime: boolean;
}

export interface Incident {
  id: string;
  type: string;
  severity: 'critical' | 'warning' | 'info';
  description: string;
  timestamp: string;
  resolved: boolean;
}

export interface VehicleDetailData extends VehicleSummary {
  vinNumber: string;
  purchaseDate: string;
  fuelCapacity: number;
  currentFuel: number;
  mileage: number;
  maintenanceStatus: string;
  lastServiceDate: string;
  
  // Current State
  currentLocation: {
    lat: number;
    lon: number;
    address: string;
  };
  currentRoute?: string;
  estimatedCompletion?: string;
  
  // History
  tripHistory: Trip[];
  maintenanceHistory: MaintenanceRecord[];
  fuelHistory: FuelRecord[];
  
  // Performance
  performance: {
    avgSpeed: number;
    fuelEfficiency: number;
    utilizationRate: number;
    uptime: number;
  };
}

export interface Trip {
  id: string;
  date: string;
  route: string;
  distance: number;
  duration: string;
  fuelUsed: number;
  status: string;
}

export interface MaintenanceRecord {
  id: string;
  date: string;
  type: string;
  cost: number;
  description: string;
  nextDue?: string;
}

export interface FuelRecord {
  id: string;
  date: string;
  amount: number;
  costPerLiter: number;
  totalCost: number;
}

export interface DriverDetailData extends DriverSummary {
  email: string;
  phone: string;
  address: string;
  licenseExpiry: string;
  licenseType: string;
  yearsExperience: number;
  
  // Current Assignment
  currentVehicle?: string;
  currentRoute?: string;
  shift: {
    startTime: string;
    estimatedEndTime: string;
    duration: string;
  };
  
  // Performance Metrics
  metrics: {
    totalDeliveries: number;
    onTimeRate: number;
    safetyIncidents: number;
    customerRating: number;
    fuelEfficiency: number;
  };
  
  // History
  deliveryHistory: DriverDelivery[];
  incidentHistory: SafetyIncident[];
  trainingHistory: TrainingRecord[];
}

export interface DriverDelivery {
  id: string;
  date: string;
  route: string;
  destination: string;
  status: string;
  onTime: boolean;
  customerRating?: number;
}

export interface SafetyIncident {
  id: string;
  date: string;
  type: string;
  severity: string;
  description: string;
  resolved: boolean;
}

export interface TrainingRecord {
  id: string;
  date: string;
  type: string;
  duration: string;
  status: 'completed' | 'pending';
}
