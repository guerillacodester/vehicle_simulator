/**
 * VEHICLES PAGE - UNIFIED FRAMEWORK EXAMPLE
 * Complete example of the new unified page architecture
 */

'use client'

import { useState, useEffect } from 'react'
import { UnifiedPage } from '@/components/shared/UnifiedPage'
import { 
  FilterConfig, 
  ActionConfig, 
  CardFieldConfig, 
  ListColumnConfig,
  BaseEntity 
} from '@/types/shared'

// Vehicle entity extending BaseEntity
interface Vehicle extends BaseEntity {
  vehicle_id: string
  license_plate: string
  make: string
  model: string
  year: number
  status: 'active' | 'inactive' | 'maintenance' | 'out_of_service'
  route_id?: string
  driver_id?: string
  location?: string
  fuel_level?: number
}

export default function VehiclesPageUnified() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [loading, setLoading] = useState(true)

  // Load vehicles data
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/vehicles/')
        if (response.ok) {
          const data = await response.json()
          setVehicles(data)
        } else {
          console.error('Failed to load vehicles:', response.statusText)
        }
      } catch (error) {
        console.error('Error loading vehicles:', error)
      } finally {
        setLoading(false)
      }
    }

    loadVehicles()
  }, [])

  // Filter configuration
  const filters: FilterConfig[] = [
    {
      key: 'search',
      type: 'search',
      label: 'Search vehicles',
      placeholder: 'Search by ID, license plate, make, model...'
    },
    {
      key: 'status',
      type: 'select',
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'maintenance', label: 'Maintenance' },
        { value: 'out_of_service', label: 'Out of Service' }
      ]
    },
    {
      key: 'make',
      type: 'multiselect',
      label: 'Make',
      options: [
        { value: 'toyota', label: 'Toyota' },
        { value: 'ford', label: 'Ford' },
        { value: 'mercedes', label: 'Mercedes' },
        { value: 'volvo', label: 'Volvo' }
      ]
    },
    {
      key: 'route_id',
      type: 'select',
      label: 'Route',
      options: [
        { value: 'route_1', label: 'Route 1' },
        { value: 'route_2', label: 'Route 2' },
        { value: 'route_3', label: 'Route 3' }
      ]
    }
  ]

  // Action configuration
  const actions: ActionConfig[] = [
    {
      action: 'view',
      label: 'View Details',
      icon: 'Eye',
      onClick: (vehicle: Vehicle) => {
        console.log('View vehicle:', vehicle.id)
        // Navigate to vehicle details
      }
    },
    {
      action: 'edit',
      label: 'Edit Vehicle',
      icon: 'Edit',
      onClick: (vehicle: Vehicle) => {
        console.log('Edit vehicle:', vehicle.id)
        // Open edit modal or navigate to edit page
      }
    },
    {
      action: 'delete',
      label: 'Delete Vehicle',
      icon: 'Trash2',
      variant: 'destructive',
      onClick: (vehicle: Vehicle) => {
        if (confirm(`Are you sure you want to delete vehicle ${vehicle.license_plate}?`)) {
          console.log('Delete vehicle:', vehicle.id)
          // Call delete API
        }
      }
    }
  ]

  // Card view field configuration
  const cardFields: CardFieldConfig[] = [
    {
      key: 'license_plate',
      label: 'License Plate',
      type: 'primary',
      showInHeader: true
    },
    {
      key: 'make',
      label: 'Make',
      type: 'secondary'
    },
    {
      key: 'model',
      label: 'Model',
      type: 'secondary'
    },
    {
      key: 'year',
      label: 'Year',
      type: 'secondary'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'badge',
      showInHeader: true
    },
    {
      key: 'route_id',
      label: 'Current Route',
      type: 'secondary'
    },
    {
      key: 'driver_id',
      label: 'Assigned Driver',
      type: 'secondary'
    },
    {
      key: 'fuel_level',
      label: 'Fuel Level',
      type: 'secondary',
      format: (value) => value ? `${value}%` : 'Unknown'
    }
  ]

  // List view column configuration
  const listColumns: ListColumnConfig[] = [
    {
      key: 'license_plate',
      label: 'Vehicle',
      type: 'avatar',
      sortable: true,
      width: 'w-48'
    },
    {
      key: 'make',
      label: 'Make',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'model',
      label: 'Model', 
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'year',
      label: 'Year',
      type: 'text',
      sortable: true,
      width: 'w-24'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'status',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'route_id',
      label: 'Route',
      type: 'badge',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'fuel_level',
      label: 'Fuel',
      type: 'text',
      sortable: true,
      width: 'w-24'
    }
  ]

  const handleCreateNew = () => {
    console.log('Create new vehicle')
    // Navigate to create vehicle page or open modal
  }

  const handleRefresh = () => {
    console.log('Refresh vehicles')
    // Reload vehicles data
    setVehicles(prev => [...prev]) // Force re-render for demo
  }

  const handleFilter = (filters: any) => {
    console.log('Apply filters:', filters)
    // Filters are applied automatically by UnifiedPage
  }

  const handleSort = (column: string, direction: 'asc' | 'desc') => {
    console.log('Sort by:', column, direction)
    // Sorting is handled automatically by UnifiedPage
  }

  return (
    <UnifiedPage
      title="Fleet Vehicles"
      subtitle="Manage your vehicle fleet with real-time tracking and status updates"
      entities={vehicles}
      loading={loading}
      filters={filters}
      actions={actions}
      cardFields={cardFields}
      listColumns={listColumns}
      onCreateNew={handleCreateNew}
      onRefresh={handleRefresh}
      onFilter={handleFilter}
      onSort={handleSort}
      createButtonText="Add Vehicle"
      emptyMessage="No vehicles found. Add your first vehicle to get started."
    />
  )
}
