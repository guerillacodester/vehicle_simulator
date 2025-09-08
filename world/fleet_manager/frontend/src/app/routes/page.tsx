/**
 * ROUTES PAGE - Unified Framework Implementation
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

// Route entity extending BaseEntity
interface Route extends BaseEntity {
  route_id: string
  route_name: string
  route_number: string
  origin: string
  destination: string
  distance_km: number
  duration_minutes: number
  status: 'active' | 'inactive' | 'maintenance' | 'suspended'
  stops_count: number
  frequency_minutes: number
  fare: number
  route_type: 'regular' | 'express' | 'night' | 'weekend'
}

export default function RoutesPage() {
  const [routes, setRoutes] = useState<Route[]>([])
  const [loading, setLoading] = useState(true)

  // Load routes data
  useEffect(() => {
    const loadRoutes = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/v1/routes/')
        if (response.ok) {
          const data = await response.json()
          // Transform data to match our interface
          const transformedRoutes = data.map((route: any) => ({
            ...route,
            name: route.route_name || `Route ${route.route_number}`,
            description: `${route.origin} → ${route.destination}`,
            entity_type: 'route'
          }))
          setRoutes(transformedRoutes)
        } else {
          console.error('Failed to load routes:', response.statusText)
        }
      } catch (error) {
        console.error('Error loading routes:', error)
      } finally {
        setLoading(false)
      }
    }

    loadRoutes()
  }, [])

  // Filter configuration
  const filters: FilterConfig[] = [
    {
      key: 'search',
      type: 'search',
      label: 'Search routes',
      placeholder: 'Search by route name, number, origin, destination...'
    },
    {
      key: 'status',
      type: 'select',
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'maintenance', label: 'Maintenance' },
        { value: 'suspended', label: 'Suspended' }
      ]
    },
    {
      key: 'route_type',
      type: 'multiselect',
      label: 'Route Type',
      options: [
        { value: 'regular', label: 'Regular' },
        { value: 'express', label: 'Express' },
        { value: 'night', label: 'Night Service' },
        { value: 'weekend', label: 'Weekend Only' }
      ]
    },
    {
      key: 'distance_km',
      type: 'select',
      label: 'Distance Range',
      options: [
        { value: '0-10', label: 'Under 10 km' },
        { value: '10-20', label: '10-20 km' },
        { value: '20-50', label: '20-50 km' },
        { value: '50+', label: 'Over 50 km' }
      ]
    }
  ]

  // Action configuration
  const actions: ActionConfig[] = [
    {
      action: 'view',
      label: 'View Route',
      icon: 'Route',
      onClick: (route: Route) => {
        console.log('View route:', route.id)
        // Navigate to route details
      }
    },
    {
      action: 'edit',
      label: 'Edit Route',
      icon: 'Edit',
      onClick: (route: Route) => {
        console.log('Edit route:', route.id)
        // Open edit modal or navigate to edit page
      }
    },
    {
      action: 'assign',
      label: 'Assign Vehicles',
      icon: 'Car',
      onClick: (route: Route) => {
        console.log('Assign vehicles to route:', route.id)
        // Open vehicle assignment modal
      }
    },
    {
      action: 'delete',
      label: 'Delete Route',
      icon: 'Trash2',
      variant: 'destructive',
      onClick: (route: Route) => {
        if (confirm(`Are you sure you want to delete route ${route.name}?`)) {
          console.log('Delete route:', route.id)
          // Call delete API
        }
      }
    }
  ]

  // Card view field configuration
  const cardFields: CardFieldConfig[] = [
    {
      key: 'name',
      label: 'Route Name',
      type: 'primary',
      showInHeader: true
    },
    {
      key: 'route_number',
      label: 'Route Number',
      type: 'secondary'
    },
    {
      key: 'description',
      label: 'Route',
      type: 'secondary'
    },
    {
      key: 'distance_km',
      label: 'Distance',
      type: 'secondary',
      format: (value) => value ? `${value} km` : 'Unknown'
    },
    {
      key: 'duration_minutes',
      label: 'Duration',
      type: 'secondary',
      format: (value) => value ? `${Math.floor(value / 60)}h ${value % 60}m` : 'Unknown'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'badge',
      showInHeader: true
    },
    {
      key: 'stops_count',
      label: 'Stops',
      type: 'secondary',
      format: (value) => value ? `${value} stops` : 'No stops'
    },
    {
      key: 'frequency_minutes',
      label: 'Frequency',
      type: 'secondary',
      format: (value) => value ? `Every ${value} min` : 'On demand'
    },
    {
      key: 'fare',
      label: 'Fare',
      type: 'secondary',
      format: (value) => value ? `$${value.toFixed(2)}` : 'Free'
    }
  ]

  // List view column configuration
  const listColumns: ListColumnConfig[] = [
    {
      key: 'name',
      label: 'Route',
      type: 'avatar',
      sortable: true,
      width: 'w-64'
    },
    {
      key: 'route_number',
      label: 'Number',
      type: 'text',
      sortable: true,
      width: 'w-24'
    },
    {
      key: 'origin',
      label: 'Origin',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'destination',
      label: 'Destination',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'distance_km',
      label: 'Distance',
      type: 'text',
      sortable: true,
      width: 'w-24'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'status',
      sortable: true,
      width: 'w-28'
    },
    {
      key: 'route_type',
      label: 'Type',
      type: 'badge',
      sortable: true,
      width: 'w-28'
    },
    {
      key: 'stops_count',
      label: 'Stops',
      type: 'text',
      sortable: true,
      width: 'w-20'
    }
  ]

  const handleCreateNew = () => {
    console.log('Create new route')
    // Navigate to create route page or open modal
  }

  const handleRefresh = async () => {
    console.log('Refresh routes')
    // Reload routes data from API
    try {
      setLoading(true)
      const response = await fetch('/api/v1/routes/')
      if (response.ok) {
        const data = await response.json()
        const transformedRoutes = data.map((route: any) => ({
          ...route,
          name: route.route_name || `Route ${route.route_number}`,
          description: `${route.origin} → ${route.destination}`,
          entity_type: 'route'
        }))
        setRoutes(transformedRoutes)
      } else {
        console.error('Failed to refresh routes:', response.statusText)
      }
    } catch (error) {
      console.error('Error refreshing routes:', error)
    } finally {
      setLoading(false)
    }
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
      title="Route Management"
      subtitle="Manage your transit routes and schedules with real-time tracking"
      entities={routes}
      loading={loading}
      filters={filters}
      actions={actions}
      cardFields={cardFields}
      listColumns={listColumns}
      onCreateNew={handleCreateNew}
      onRefresh={handleRefresh}
      onFilter={handleFilter}
      onSort={handleSort}
      createButtonText="Add Route"
      emptyMessage="No routes found. Create your first route to get started."
    />
  )
}
