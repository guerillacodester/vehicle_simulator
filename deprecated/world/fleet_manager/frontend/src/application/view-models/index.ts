/**
 * VIEW MODELS - MVVM Presentation Logic
 * These handle UI state management and data transformation
 * They contain no business logic - only presentation concerns
 */

// TODO: React will be available once we run npm install
// For now, we'll define the hook types manually to avoid compilation errors
type SetStateAction<S> = S | ((prevState: S) => S);
type Dispatch<A> = (value: A) => void;

// Temporary React hook types until React is installed
function useState<S>(initialState: S | (() => S)): [S, Dispatch<SetStateAction<S>>] {
  throw new Error('React not yet installed - this is a type definition only');
}

// More flexible useCallback type that preserves function signatures
function useCallback<T extends (...args: never[]) => unknown>(callback: T, deps: unknown[]): T {
  throw new Error('React not yet installed - this is a type definition only');
}

import { Vehicle, Driver, VehicleStatus } from '@/domain/entities';
import { VehicleUseCases, DriverUseCases } from '@/application/use-cases';

export interface VehicleFormData {
  countryId: string;
  depotId: string;
  plateNumber: string;
  regCode: string;
  model: string;
  capacity: number;
  status: VehicleStatus;
}

export interface VehicleListViewModel {
  vehicles: Vehicle[];
  loading: boolean;
  error: string | null;
  searchTerm: string;
  statusFilter: VehicleStatus | 'ALL';
  sortBy: 'plateNumber' | 'model' | 'capacity' | 'status';
  sortDirection: 'asc' | 'desc';
  
  // Actions
  loadVehicles: () => Promise<void>;
  setSearchTerm: (term: string) => void;
  setStatusFilter: (status: VehicleStatus | 'ALL') => void;
  setSorting: (sortBy: string, direction: 'asc' | 'desc') => void;
  deleteVehicle: (id: string) => Promise<void>;
  
  // Computed
  filteredVehicles: Vehicle[];
}

export function useVehicleListViewModel(vehicleUseCases: VehicleUseCases): VehicleListViewModel {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<VehicleStatus | 'ALL'>('ALL');
  const [sortBy, setSortBy] = useState<'plateNumber' | 'model' | 'capacity' | 'status'>('plateNumber');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const loadVehicles = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const result = await vehicleUseCases.getAllVehicles();
      setVehicles(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load vehicles');
    } finally {
      setLoading(false);
    }
  }, [vehicleUseCases]);

  const deleteVehicle = useCallback(async (id: string): Promise<void> => {
    setError(null);
    try {
      await vehicleUseCases.deleteVehicle(id);
      setVehicles((prev: Vehicle[]) => prev.filter((v: Vehicle) => v.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete vehicle');
    }
  }, [vehicleUseCases]);

  const setSorting = useCallback((newSortBy: string, direction: 'asc' | 'desc'): void => {
    setSortBy(newSortBy as 'plateNumber' | 'model' | 'capacity' | 'status');
    setSortDirection(direction);
  }, []);

  // Computed filtered and sorted vehicles
  const filteredVehicles = vehicles
    .filter((vehicle: Vehicle) => {
      const matchesSearch = vehicle.plateNumber.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           vehicle.model.toLowerCase().includes(searchTerm.toLowerCase());
      const matchesStatus = statusFilter === 'ALL' || vehicle.status === statusFilter;
      return matchesSearch && matchesStatus;
    })
    .sort((a: Vehicle, b: Vehicle) => {
      const multiplier = sortDirection === 'asc' ? 1 : -1;
      switch (sortBy) {
        case 'plateNumber':
          return a.plateNumber.localeCompare(b.plateNumber) * multiplier;
        case 'model':
          return a.model.localeCompare(b.model) * multiplier;
        case 'capacity':
          return (a.capacity - b.capacity) * multiplier;
        case 'status':
          return (a.status || '').localeCompare(b.status || '') * multiplier;
        default:
          return 0;
      }
    });

  return {
    vehicles,
    loading,
    error,
    searchTerm,
    statusFilter,
    sortBy,
    sortDirection,
    loadVehicles,
    setSearchTerm,
    setStatusFilter,
    setSorting,
    deleteVehicle,
    filteredVehicles,
  };
}

export interface VehicleFormViewModel {
  formData: VehicleFormData;
  loading: boolean;
  error: string | null;
  validationErrors: Record<string, string>;
  
  // Actions
  setField: (field: keyof VehicleFormData, value: string | number | VehicleStatus) => void;
  validateForm: () => boolean;
  submitForm: () => Promise<boolean>;
  resetForm: () => void;
}

export function useVehicleFormViewModel(
  vehicleUseCases: VehicleUseCases,
  editingVehicle?: Vehicle
): VehicleFormViewModel {
  const [formData, setFormData] = useState<VehicleFormData>({
    countryId: editingVehicle?.countryId || '',
    depotId: editingVehicle?.depotId || '',
    plateNumber: editingVehicle?.plateNumber || '',
    regCode: editingVehicle?.regCode || '',
    model: editingVehicle?.model || '',
    capacity: editingVehicle?.capacity || 0,
    status: (editingVehicle?.status as VehicleStatus) || ('ACTIVE' as VehicleStatus),
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const setField = useCallback((field: keyof VehicleFormData, value: string | number | VehicleStatus): void => {
    setFormData((prev: VehicleFormData) => ({ ...prev, [field]: value }));
    // Clear validation error for this field
    if (validationErrors[field]) {
      setValidationErrors((prev: Record<string, string>) => ({ ...prev, [field]: '' }));
    }
  }, [validationErrors]);

  const validateForm = useCallback((): boolean => {
    const errors: Record<string, string> = {};

    if (!formData.plateNumber.trim()) {
      errors.plateNumber = 'Plate number is required';
    }

    if (!formData.model.trim()) {
      errors.model = 'Model is required';
    }

    if (formData.capacity <= 0) {
      errors.capacity = 'Capacity must be greater than 0';
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData]);

  const submitForm = useCallback(async (): Promise<boolean> => {
    if (!validateForm()) {
      return false;
    }

    setLoading(true);
    setError(null);

    try {
      if (editingVehicle) {
        await vehicleUseCases.updateVehicle(editingVehicle.id, formData);
      } else {
        await vehicleUseCases.createVehicle(formData);
      }
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save vehicle');
      return false;
    } finally {
      setLoading(false);
    }
  }, [formData, validateForm, vehicleUseCases, editingVehicle]);

  const resetForm = useCallback(() => {
    setFormData({
      countryId: '',
      depotId: '',
      plateNumber: '',
      regCode: '',
      model: '',
      capacity: 0,
      status: 'ACTIVE' as VehicleStatus,
    });
    setValidationErrors({});
    setError(null);
  }, []);

  return {
    formData,
    loading,
    error,
    validationErrors,
    setField,
    validateForm,
    submitForm,
    resetForm,
  };
}

// Similar ViewModels for Driver management
export interface DriverFormData {
  employeeId: string;
  firstName: string;
  lastName: string;
  licenseNumber: string;
  licenseExpiry: Date;
  contactInfo: string;
  status: 'ACTIVE' | 'INACTIVE' | 'ON_LEAVE';
}

export function useDriverListViewModel(driverUseCases: DriverUseCases) {
  // Similar implementation to useVehicleListViewModel
  // Omitted for brevity but follows same pattern
}

export function useDriverFormViewModel(
  driverUseCases: DriverUseCases,
  editingDriver?: Driver
) {
  // Similar implementation to useVehicleFormViewModel
  // Omitted for brevity but follows same pattern
}
