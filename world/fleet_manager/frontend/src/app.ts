/**
 * MAIN APPLICATION ENTRY POINT
 * This orchestrates the Clean Architecture layers and sets up dependency injection
 */

import { DependencyContainer } from '@/infrastructure/repositories';
import { VehicleUseCases, DriverUseCases } from '@/application/use-cases';
import { VehicleAssignmentService, DriverAssignmentService, SchedulingService, FileValidationService } from '@/domain/services';

// Application Configuration
interface AppConfig {
  apiBaseURL: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    enableFileUpload: boolean;
    enableRealtimeUpdates: boolean;
    enableAdvancedScheduling: boolean;
  };
}

// Default configuration
const defaultConfig: AppConfig = {
  apiBaseURL: 'http://localhost:8000', // TODO: Will be configured via environment variables
  environment: 'development', // TODO: Will be configured via environment variables
  features: {
    enableFileUpload: true,
    enableRealtimeUpdates: false, // TODO: Implement WebSocket integration
    enableAdvancedScheduling: true,
  }
};

// Application Container - Dependency Injection Root
export class FleetManagementApp {
  private container: DependencyContainer;
  private vehicleUseCases: VehicleUseCases;
  private driverUseCases: DriverUseCases;
  private config: AppConfig;

  constructor(config: AppConfig = defaultConfig) {
    this.config = config;
    
    // Initialize Infrastructure Layer
    this.container = new DependencyContainer({
      baseURL: config.apiBaseURL,
      timeout: 10000,
      enableMock: false, // Use real API by default, fallback to mock on failure
      headers: {
        'X-App-Version': '1.0.0',
        'X-Environment': config.environment
      }
    });

    // Initialize Domain Services
    const vehicleAssignmentService = new VehicleAssignmentService();
    const driverAssignmentService = new DriverAssignmentService();
    const schedulingService = new SchedulingService();
    const fileValidationService = new FileValidationService();

    // Initialize Application Layer (Use Cases)
    this.vehicleUseCases = new VehicleUseCases(
      this.container.getVehicleRepository(),
      vehicleAssignmentService,
      fileValidationService
    );

    this.driverUseCases = new DriverUseCases(
      this.container.getDriverRepository(),
      driverAssignmentService
    );
  }

  // Getters for Use Cases (to be used by ViewModels)
  getVehicleUseCases(): VehicleUseCases {
    return this.vehicleUseCases;
  }

  getDriverUseCases(): DriverUseCases {
    return this.driverUseCases;
  }

  getConfig(): AppConfig {
    return this.config;
  }

  // Application initialization
  async initialize(): Promise<void> {
    console.log('Fleet Management Application initializing...');
    
    try {
      // Perform any startup checks
      await this.healthCheck();
      
      console.log('Fleet Management Application initialized successfully');
    } catch (error) {
      console.error('Failed to initialize application:', error);
      throw error;
    }
  }

  // Health check to verify API connectivity
  private async healthCheck(): Promise<void> {
    try {
      // Try to fetch a single vehicle to test API connectivity
      // This will throw if the API is unreachable
      await this.vehicleUseCases.getAllVehicles();
      console.log('API connectivity verified');
    } catch (error) {
      console.warn('API connectivity check failed - app will work in offline mode');
      // Don't throw here - allow app to start in offline mode
    }
  }
}

// Global app instance (Singleton pattern for the application container)
let appInstance: FleetManagementApp | null = null;

export function getAppInstance(config?: AppConfig): FleetManagementApp {
  if (!appInstance) {
    appInstance = new FleetManagementApp(config);
  }
  return appInstance;
}

// React Context Provider for dependency injection
// TODO: This will be implemented with actual React Context once React is installed
export interface AppContextValue {
  app: FleetManagementApp;
  vehicleUseCases: VehicleUseCases;
  driverUseCases: DriverUseCases;
  config: AppConfig;
}

// Mock React Context structure for now
export const AppContext = {
  Provider: (props: { value: AppContextValue; children: unknown }) => {
    throw new Error('React not yet installed - this is a type definition only');
  },
  Consumer: (props: { children: (value: AppContextValue) => unknown }) => {
    throw new Error('React not yet installed - this is a type definition only');
  }
};

// Hook to access app context
export function useApp(): AppContextValue {
  throw new Error('React not yet installed - this is a type definition only');
}

// Higher-order component for dependency injection
type ComponentType<P = Record<string, unknown>> = (props: P) => unknown;

export function withApp<P extends object>(Component: ComponentType<P>) {
  return (props: P) => {
    throw new Error('React not yet installed - this is a type definition only');
  };
}

// Application Routes Configuration
export interface AppRoute {
  path: string;
  component: string;
  title: string;
  requiresAuth?: boolean;
  permissions?: string[];
}

export const appRoutes: AppRoute[] = [
  {
    path: '/',
    component: 'DashboardView',
    title: 'Fleet Dashboard'
  },
  {
    path: '/vehicles',
    component: 'VehicleListView',
    title: 'Vehicle Management'
  },
  {
    path: '/vehicles/new',
    component: 'VehicleFormView',
    title: 'Add Vehicle'
  },
  {
    path: '/vehicles/:id/edit',
    component: 'VehicleFormView',
    title: 'Edit Vehicle'
  },
  {
    path: '/drivers',
    component: 'DriverListView',
    title: 'Driver Management'
  },
  {
    path: '/drivers/new',
    component: 'DriverFormView',
    title: 'Add Driver'
  },
  {
    path: '/routes',
    component: 'RouteListView',
    title: 'Route Management'
  },
  {
    path: '/timetables',
    component: 'TimetableView',
    title: 'Timetable Management'
  },
  {
    path: '/scheduling',
    component: 'SchedulingView',
    title: 'Driver & Vehicle Scheduling'
  },
  {
    path: '/import',
    component: 'FileUploadView',
    title: 'Bulk Data Import'
  }
];

// Error Boundary for the application
interface ErrorInfo {
  componentStack: string;
  errorBoundary?: string;
  errorBoundaryStack?: string;
}

export class AppErrorBoundary {
  static handleError(error: Error, errorInfo: ErrorInfo) {
    console.error('Application error:', error, errorInfo);
    
    // TODO: Send error to logging service
    // TODO: Show user-friendly error message
    // TODO: Attempt recovery strategies
  }
}

export default FleetManagementApp;
