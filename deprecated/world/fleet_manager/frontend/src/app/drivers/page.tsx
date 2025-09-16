/**
 * DRIVERS PAGE - Unified Framework Implementation
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

// Driver entity extending BaseEntity
interface Driver extends BaseEntity {
  driver_id: string
  license_number: string
  first_name: string
  last_name: string
  phone: string
  email: string
  status: 'active' | 'inactive' | 'on_leave' | 'suspended'
  hire_date: string
  license_expiry: string
  vehicle_id?: string
  route_id?: string
  experience_years?: number
  rating?: number
}

export default function DriversPage() {
  const [drivers, setDrivers] = useState<Driver[]>([])
  const [loading, setLoading] = useState(true)
  const [countries, setCountries] = useState<any[]>([])

  // Load drivers data
  useEffect(() => {
    const loadDrivers = async () => {
      try {
        setLoading(true)
        
        // Load drivers
        const driversResponse = await fetch('/api/v1/drivers/')
        if (driversResponse.ok) {
          const data = await driversResponse.json()
          // Transform data to match our interface
          const transformedDrivers = data.map((driver: any) => ({
            ...driver,
            name: driver.name,
            description: `License: ${driver.license_no}`,
            entity_type: 'driver',
            driver_id: driver.driver_id,
            license_number: driver.license_no,
            first_name: driver.name.split(' ')[0],
            last_name: driver.name.split(' ').slice(1).join(' '),
            status: driver.employment_status === 'active' ? 'active' : 'inactive',
            hire_date: new Date(driver.created_at).toISOString().split('T')[0]
          }))
          setDrivers(transformedDrivers)
        } else {
          console.error('Failed to load drivers:', driversResponse.statusText)
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
        console.error('Error loading data:', error)
      } finally {
        setLoading(false)
      }
    }

    loadDrivers()
  }, [])

  // Filter configuration
  const filters: FilterConfig[] = [
    {
      key: 'search',
      type: 'search',
      label: 'Search',
      placeholder: 'Search by name, license...'
    },
    {
      key: 'employment_status',
      type: 'select',
      label: 'Employment Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'on_leave', label: 'On Leave' },
        { value: 'suspended', label: 'Suspended' }
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
      label: 'View Profile',
      icon: 'User',
      onClick: (driver: Driver) => {
        console.log('View driver:', driver.id)
        // Navigate to driver profile
      }
    },
    {
      action: 'edit',
      label: 'Edit Driver',
      icon: 'Edit',
      onClick: (driver: Driver) => {
        console.log('Edit driver:', driver.id)
        // Open edit modal or navigate to edit page
      }
    },
    {
      action: 'assign',
      label: 'Assign Vehicle',
      icon: 'Car',
      onClick: (driver: Driver) => {
        console.log('Assign vehicle to driver:', driver.id)
        // Open vehicle assignment modal
      }
    },
    {
      action: 'delete',
      label: 'Remove Driver',
      icon: 'Trash2',
      variant: 'destructive',
      onClick: (driver: Driver) => {
        if (confirm(`Are you sure you want to remove driver ${driver.name}?`)) {
          console.log('Delete driver:', driver.id)
          // Call delete API
        }
      }
    }
  ]

  // Card view field configuration
  const cardFields: CardFieldConfig[] = [
    {
      key: 'name',
      label: 'Full Name',
      type: 'primary',
      showInHeader: true
    },
    {
      key: 'license_number',
      label: 'License Number',
      type: 'secondary'
    },
    {
      key: 'phone',
      label: 'Phone',
      type: 'secondary'
    },
    {
      key: 'email',
      label: 'Email',
      type: 'secondary'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'badge',
      showInHeader: true
    },
    {
      key: 'vehicle_id',
      label: 'Assigned Vehicle',
      type: 'secondary'
    },
    {
      key: 'route_id',
      label: 'Current Route',
      type: 'secondary'
    },
    {
      key: 'experience_years',
      label: 'Experience',
      type: 'secondary',
      format: (value) => value ? `${value} years` : 'Not specified'
    },
    {
      key: 'rating',
      label: 'Rating',
      type: 'secondary',
      format: (value) => value ? `${value}/5.0` : 'No rating'
    }
  ]

  // List view column configuration
  const listColumns: ListColumnConfig[] = [
    {
      key: 'name',
      label: 'Driver',
      type: 'avatar',
      sortable: true,
      width: 'w-48'
    },
    {
      key: 'license_number',
      label: 'License',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'phone',
      label: 'Phone',
      type: 'text',
      sortable: false,
      width: 'w-32'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'status',
      sortable: true,
      width: 'w-28'
    },
    {
      key: 'vehicle_id',
      label: 'Vehicle',
      type: 'badge',
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
      key: 'hire_date',
      label: 'Hire Date',
      type: 'date',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'license_expiry',
      label: 'License Expiry',
      type: 'date',
      sortable: true,
      width: 'w-32'
    }
  ]

  const handleCreateNew = () => {
    console.log('Create new driver')
    // Navigate to create driver page or open modal
  }

  const handleRefresh = () => {
    console.log('Refresh drivers')
    // Reload drivers data
    setDrivers(prev => [...prev]) // Force re-render for demo
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
      title="Driver Management"
      subtitle="Manage your fleet drivers with real-time status tracking and assignments"
      entities={drivers}
      loading={loading}
      filters={filters}
      actions={actions}
      cardFields={cardFields}
      listColumns={listColumns}
      onCreateNew={handleCreateNew}
      onRefresh={handleRefresh}
      onFilter={handleFilter}
      onSort={handleSort}
      createButtonText="Add Driver"
      emptyMessage="No drivers found. Add your first driver to get started."
    />
  )
}
