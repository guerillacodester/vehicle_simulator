/**
 * VEHICLES PAGE - Unified Framework Implementation  
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

// Flag mapping for country codes
const flagMapping: Record<string, string> = {
  'BB': '🇧🇧', // Barbados
  'JM': '🇯🇲', // Jamaica  
  'TT': '🇹🇹', // Trinidad and Tobago
  'GY': '🇬🇾', // Guyana
  'SR': '🇸🇷', // Suriname
  'BS': '🇧🇸', // Bahamas
  'BZ': '🇧🇿', // Belize
  'LC': '🇱🇨', // Saint Lucia
  'GD': '🇬🇩', // Grenada
  'VC': '🇻🇨', // Saint Vincent and the Grenadines
  'AG': '🇦🇬', // Antigua and Barbuda
  'DM': '🇩🇲', // Dominica
  'KN': '🇰🇳', // Saint Kitts and Nevis
}

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

export default function VehiclesPage() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [loading, setLoading] = useState(true)
  const [countries, setCountries] = useState<any[]>([])

  // Load vehicles data
  useEffect(() => {
    const loadVehicles = async () => {
      try {
        setLoading(true)
        
        // Load vehicles
        const vehiclesResponse = await fetch('/api/v1/vehicles/')
        if (vehiclesResponse.ok) {
          const data = await vehiclesResponse.json()
          // Transform data to match our interface
          const transformedVehicles = data.map((vehicle: any) => ({
            ...vehicle,
            name: vehicle.reg_code || `Vehicle ${vehicle.vehicle_id.slice(0, 8)}`,
            description: `Status: ${vehicle.status}`,
            entity_type: 'vehicle',
            license_plate: vehicle.reg_code,
            last_maintenance: new Date(vehicle.updated_at).toISOString().split('T')[0]
          }))
          setVehicles(transformedVehicles)
        } else {
          console.error('Failed to load vehicles:', vehiclesResponse.statusText)
        }

        // Load countries
        const countriesResponse = await fetch('/api/v1/countries/')
        if (countriesResponse.ok) {
          const countriesData = await countriesResponse.json()
          setCountries(countriesData)
        } else {
          console.error('Failed to load countries:', countriesResponse.statusText)
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
      label: 'Search',
      placeholder: 'Search by registration, status...'
    },
    {
      key: 'status',
      type: 'select',
      label: 'Status',
      options: [
        { value: 'available', label: 'Available' },
        { value: 'maintenance', label: 'Maintenance' },
        { value: 'retired', label: 'Retired' }
      ]
    },
    {
      key: 'country_id',
      type: 'select',
      label: 'Country',
      options: countries.map(country => ({
        value: country.country_id,
        label: `${flagMapping[country.iso_code] || '🌍'} ${country.name}`
      }))
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
      action: 'assign',
      label: 'Assign Driver',
      icon: 'User',
      onClick: (vehicle: Vehicle) => {
        console.log('Assign driver to vehicle:', vehicle.id)
        // Open driver assignment modal
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
