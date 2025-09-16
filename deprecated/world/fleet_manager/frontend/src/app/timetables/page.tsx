/**
 * TIMETABLES PAGE - Unified Framework Implementation
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

// Timetable entity extending BaseEntity
interface Timetable extends BaseEntity {
  timetable_id: string
  timetable_name: string
  route_id: string
  route_name: string
  effective_date: string
  expiry_date: string
  status: 'active' | 'inactive' | 'draft' | 'archived'
  service_type: 'weekday' | 'weekend' | 'holiday' | 'special'
  trips_count: number
  first_departure: string
  last_departure: string
  frequency_minutes: number
}

export default function TimetablesPage() {
  const [timetables, setTimetables] = useState<Timetable[]>([])
  const [loading, setLoading] = useState(true)

  // Load timetables data
  useEffect(() => {
    const loadTimetables = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/v1/timetables/')
        if (response.ok) {
          const data = await response.json()
          // Transform data to match our interface
          const transformedTimetables = data.map((timetable: any) => ({
            ...timetable,
            name: timetable.timetable_name,
            description: `${timetable.route_name} - ${timetable.service_type}`,
            entity_type: 'timetable'
          }))
          setTimetables(transformedTimetables)
        } else {
          console.error('Failed to load timetables:', response.statusText)
        }
      } catch (error) {
        console.error('Error loading timetables:', error)
      } finally {
        setLoading(false)
      }
    }

    loadTimetables()
  }, [])

  // Filter configuration
  const filters: FilterConfig[] = [
    {
      key: 'search',
      type: 'search',
      label: 'Search timetables',
      placeholder: 'Search by timetable name, route...'
    },
    {
      key: 'status',
      type: 'select',
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'draft', label: 'Draft' },
        { value: 'archived', label: 'Archived' }
      ]
    },
    {
      key: 'service_type',
      type: 'multiselect',
      label: 'Service Type',
      options: [
        { value: 'weekday', label: 'Weekday' },
        { value: 'weekend', label: 'Weekend' },
        { value: 'holiday', label: 'Holiday' },
        { value: 'special', label: 'Special' }
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
    },
    {
      key: 'effective_date',
      type: 'date',
      label: 'Effective Date'
    }
  ]

  // Action configuration
  const actions: ActionConfig[] = [
    {
      action: 'view',
      label: 'View Timetable',
      icon: 'Calendar',
      onClick: (timetable: Timetable) => {
        console.log('View timetable:', timetable.id)
        // Navigate to timetable details
      }
    },
    {
      action: 'edit',
      label: 'Edit Timetable',
      icon: 'Edit',
      onClick: (timetable: Timetable) => {
        console.log('Edit timetable:', timetable.id)
        // Open edit modal or navigate to edit page
      }
    },
    {
      action: 'assign',
      label: 'Assign Route',
      icon: 'Route',
      onClick: (timetable: Timetable) => {
        console.log('Assign route to timetable:', timetable.id)
        // Open route assignment modal
      }
    },
    {
      action: 'delete',
      label: 'Delete Timetable',
      icon: 'Trash2',
      variant: 'destructive',
      onClick: (timetable: Timetable) => {
        if (confirm(`Are you sure you want to delete timetable ${timetable.name}?`)) {
          console.log('Delete timetable:', timetable.id)
          // Call delete API
        }
      }
    }
  ]

  // Card view field configuration
  const cardFields: CardFieldConfig[] = [
    {
      key: 'name',
      label: 'Timetable Name',
      type: 'primary',
      showInHeader: true
    },
    {
      key: 'route_name',
      label: 'Route',
      type: 'secondary'
    },
    {
      key: 'service_type',
      label: 'Service Type',
      type: 'badge'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'badge',
      showInHeader: true
    },
    {
      key: 'effective_date',
      label: 'Effective Date',
      type: 'date'
    },
    {
      key: 'expiry_date',
      label: 'Expiry Date',
      type: 'date'
    },
    {
      key: 'trips_count',
      label: 'Total Trips',
      type: 'secondary',
      format: (value) => value ? `${value} trips` : 'No trips'
    },
    {
      key: 'first_departure',
      label: 'First Departure',
      type: 'secondary'
    },
    {
      key: 'last_departure',
      label: 'Last Departure',
      type: 'secondary'
    }
  ]

  // List view column configuration
  const listColumns: ListColumnConfig[] = [
    {
      key: 'name',
      label: 'Timetable',
      type: 'avatar',
      sortable: true,
      width: 'w-48'
    },
    {
      key: 'route_name',
      label: 'Route',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'service_type',
      label: 'Service',
      type: 'badge',
      sortable: true,
      width: 'w-28'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'status',
      sortable: true,
      width: 'w-24'
    },
    {
      key: 'effective_date',
      label: 'Effective',
      type: 'date',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'expiry_date',
      label: 'Expiry',
      type: 'date',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'trips_count',
      label: 'Trips',
      type: 'text',
      sortable: true,
      width: 'w-20'
    },
    {
      key: 'first_departure',
      label: 'First',
      type: 'text',
      sortable: false,
      width: 'w-24'
    }
  ]

  const handleCreateNew = () => {
    console.log('Create new timetable')
    // Navigate to create timetable page or open modal
  }

  const handleRefresh = () => {
    console.log('Refresh timetables')
    // Reload timetables data
    setTimetables(prev => [...prev]) // Force re-render for demo
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
      title="Timetable Management"
      subtitle="Manage transit schedules and timetables with real-time updates"
      entities={timetables}
      loading={loading}
      filters={filters}
      actions={actions}
      cardFields={cardFields}
      listColumns={listColumns}
      onCreateNew={handleCreateNew}
      onRefresh={handleRefresh}
      onFilter={handleFilter}
      onSort={handleSort}
      createButtonText="Create Timetable"
      emptyMessage="No timetables found. Create your first timetable to get started."
    />
  )
}
