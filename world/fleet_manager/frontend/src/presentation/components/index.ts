/**
 * PRESENTATION LAYER - React Components (Views in MVVM)
 * These components handle UI rendering and user interactions
 * They depend on ViewModels for state and business logic
 */

import { VehicleListViewModel, VehicleFormViewModel } from '@/application/view-models';
import { Vehicle, Driver, Route, Stop, VehicleStatus } from '@/domain/entities';

// TODO: These components will use React and Material-UI once installed
// For now, we're defining the component structure and props

interface VehicleListViewProps {
  viewModel: VehicleListViewModel;
}

export function VehicleListView({ viewModel }: VehicleListViewProps) {
  const {
    filteredVehicles,
    loading,
    error,
    searchTerm,
    statusFilter,
    sortBy,
    sortDirection,
    setSearchTerm,
    setStatusFilter,
    setSorting,
    deleteVehicle,
    loadVehicles
  } = viewModel;

  // TODO: Replace with actual Material-UI components
  return {
    type: 'VehicleListView',
    props: {
      // Search and Filter Controls
      searchInput: {
        value: searchTerm,
        onChange: setSearchTerm,
        placeholder: 'Search by plate number or model...'
      },
      
      statusFilter: {
        value: statusFilter,
        onChange: setStatusFilter,
        options: ['ALL', 'ACTIVE', 'MAINTENANCE', 'OUT_OF_SERVICE']
      },

      // Data Table
      dataTable: {
        loading,
        error,
        columns: [
          { 
            id: 'plateNumber', 
            label: 'Plate Number', 
            sortable: true,
            sortBy: sortBy === 'plateNumber',
            sortDirection: sortBy === 'plateNumber' ? sortDirection : undefined
          },
          { 
            id: 'model', 
            label: 'Model', 
            sortable: true,
            sortBy: sortBy === 'model',
            sortDirection: sortBy === 'model' ? sortDirection : undefined
          },
          { 
            id: 'capacity', 
            label: 'Capacity', 
            sortable: true,
            sortBy: sortBy === 'capacity',
            sortDirection: sortBy === 'capacity' ? sortDirection : undefined
          },
          { 
            id: 'status', 
            label: 'Status', 
            sortable: true,
            sortBy: sortBy === 'status',
            sortDirection: sortBy === 'status' ? sortDirection : undefined
          },
          { id: 'actions', label: 'Actions', sortable: false }
        ],
        rows: filteredVehicles.map(vehicle => ({
          id: vehicle.id,
          plateNumber: vehicle.plateNumber,
          model: vehicle.model,
          capacity: vehicle.capacity,
          status: vehicle.status,
          actions: {
            edit: () => console.log('Edit vehicle', vehicle.id),
            delete: () => deleteVehicle(vehicle.id),
            view: () => console.log('View vehicle', vehicle.id)
          }
        })),
        onSort: setSorting
      },

      // Action Buttons
      actions: {
        addNew: () => console.log('Add new vehicle'),
        bulkImport: () => console.log('Bulk import vehicles'),
        refresh: loadVehicles
      }
    }
  };
}

interface VehicleFormViewProps {
  viewModel: VehicleFormViewModel;
  onSuccess?: () => void;
  onCancel?: () => void;
}

export function VehicleFormView({ viewModel, onSuccess, onCancel }: VehicleFormViewProps) {
  const {
    formData,
    loading,
    error,
    validationErrors,
    setField,
    submitForm,
    resetForm
  } = viewModel;

  const handleSubmit = async () => {
    const success = await submitForm();
    if (success && onSuccess) {
      onSuccess();
    }
  };

  // TODO: Replace with actual Material-UI form components
  return {
    type: 'VehicleFormView',
    props: {
      form: {
        loading,
        error,
        onSubmit: handleSubmit,
        onReset: resetForm,
        onCancel,
        
        fields: [
          {
            name: 'plateNumber',
            label: 'Plate Number',
            type: 'text',
            value: formData.plateNumber,
            onChange: (value: string) => setField('plateNumber', value),
            error: validationErrors.plateNumber,
            required: true
          },
          {
            name: 'model',
            label: 'Vehicle Model',
            type: 'text',
            value: formData.model,
            onChange: (value: string) => setField('model', value),
            error: validationErrors.model,
            required: true
          },
          {
            name: 'capacity',
            label: 'Passenger Capacity',
            type: 'number',
            value: formData.capacity,
            onChange: (value: number) => setField('capacity', value),
            error: validationErrors.capacity,
            required: true,
            min: 1
          },
          {
            name: 'regCode',
            label: 'Registration Code',
            type: 'text',
            value: formData.regCode,
            onChange: (value: string) => setField('regCode', value),
            required: false
          },
          {
            name: 'status',
            label: 'Status',
            type: 'select',
            value: formData.status,
            onChange: (value: VehicleStatus) => setField('status', value),
            options: [
              { value: 'ACTIVE', label: 'Active' },
              { value: 'MAINTENANCE', label: 'In Maintenance' },
              { value: 'OUT_OF_SERVICE', label: 'Out of Service' }
            ],
            required: true
          }
        ]
      }
    }
  };
}

// Dashboard View - Main Fleet Management Overview
interface DashboardViewProps {
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
}

export function DashboardView({ vehicleStats, driverStats, routeStats }: DashboardViewProps) {
  // TODO: Replace with actual Material-UI dashboard components
  return {
    type: 'DashboardView',
    props: {
      title: 'Fleet Management Dashboard',
      
      statsCards: [
        {
          title: 'Vehicles',
          total: vehicleStats.total,
          breakdown: [
            { label: 'Active', value: vehicleStats.active, color: 'success' },
            { label: 'Maintenance', value: vehicleStats.maintenance, color: 'warning' },
            { label: 'Out of Service', value: vehicleStats.outOfService, color: 'error' }
          ]
        },
        {
          title: 'Drivers',
          total: driverStats.total,
          breakdown: [
            { label: 'Available', value: driverStats.available, color: 'success' },
            { label: 'On Duty', value: driverStats.onDuty, color: 'info' },
            { label: 'On Leave', value: driverStats.onLeave, color: 'warning' }
          ]
        },
        {
          title: 'Routes',
          total: routeStats.total,
          breakdown: [
            { label: 'Active', value: routeStats.active, color: 'success' }
          ]
        }
      ],

      quickActions: [
        { label: 'Add Vehicle', action: () => console.log('Navigate to add vehicle') },
        { label: 'Add Driver', action: () => console.log('Navigate to add driver') },
        { label: 'Create Route', action: () => console.log('Navigate to create route') },
        { label: 'Schedule Maintenance', action: () => console.log('Navigate to maintenance scheduler') },
        { label: 'Import Data', action: () => console.log('Open import dialog') }
      ],

      recentActivity: {
        title: 'Recent Activity',
        items: [
          { time: '2 minutes ago', action: 'Vehicle BBX-1234 assigned to Route 15' },
          { time: '15 minutes ago', action: 'Driver John Smith started shift' },
          { time: '1 hour ago', action: 'Vehicle maintenance completed for ABC-5678' },
          { time: '2 hours ago', action: 'New route "Downtown Express" created' }
        ]
      }
    }
  };
}

// File Upload View for Bulk Operations
interface FileUploadResult {
  successful: Array<Vehicle | Driver | Route | Stop>;
  failed: Array<{ row: number; error: string }>;
  totalProcessed: number;
}

interface FileUploadViewProps {
  entityType: 'vehicles' | 'drivers' | 'routes' | 'stops';
  onFileUploaded: (results: FileUploadResult) => void;
  onCancel: () => void;
}

export function FileUploadView({ entityType, onFileUploaded, onCancel }: FileUploadViewProps) {
  // TODO: Replace with actual Material-UI file upload components
  return {
    type: 'FileUploadView',
    props: {
      title: `Bulk Import ${entityType.charAt(0).toUpperCase() + entityType.slice(1)}`,
      
      uploadArea: {
        acceptedFileTypes: entityType === 'routes' || entityType === 'stops' 
          ? ['.csv', '.geojson'] 
          : ['.csv'],
        maxFileSize: '10MB',
        onFileSelect: (file: File) => console.log('File selected:', file.name),
        onFileUpload: (file: File) => console.log('File uploaded:', file.name)
      },

      templateDownload: {
        label: `Download ${entityType} template`,
        action: () => console.log(`Download template for ${entityType}`)
      },

      validationResults: {
        // Will be populated after file validation
        show: false,
        errors: [],
        warnings: [],
        successCount: 0,
        failureCount: 0
      },

      actions: {
        process: () => console.log('Process uploaded file'),
        cancel: onCancel,
        downloadResults: () => console.log('Download processing results')
      }
    }
  };
}
