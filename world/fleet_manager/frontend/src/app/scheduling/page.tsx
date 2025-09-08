/**
 * SCHEDULING PAGE - Unified Framework Implementation
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

// Schedule entity extending BaseEntity
interface Schedule extends BaseEntity {
  schedule_id: string
  schedule_name: string
  schedule_type: 'vehicle' | 'driver' | 'route'
  vehicle_id?: string
  driver_id?: string
  route_id?: string
  start_date: string
  end_date: string
  start_time: string
  end_time: string
  status: 'active' | 'inactive' | 'pending' | 'completed' | 'cancelled'
  recurring: boolean
  recurring_pattern?: 'daily' | 'weekly' | 'monthly'
  shift_hours: number
  break_duration: number
}

export default function SchedulingPage() {
  const [schedules, setSchedules] = useState<Schedule[]>([])
  const [loading, setLoading] = useState(true)

  // Load schedules data
  useEffect(() => {
    const loadSchedules = async () => {
      try {
        setLoading(true)
        const response = await fetch('/api/v1/schedules/')
        if (response.ok) {
          const data = await response.json()
          // Transform data to match our interface
          const transformedSchedules = data.map((schedule: any) => ({
            ...schedule,
            name: schedule.schedule_name || `${schedule.schedule_type} Schedule`,
            description: `${schedule.start_time} - ${schedule.end_time}`,
            entity_type: 'schedule'
          }))
          setSchedules(transformedSchedules)
        } else {
          console.error('Failed to load schedules:', response.statusText)
        }
      } catch (error) {
        console.error('Error loading schedules:', error)
      } finally {
        setLoading(false)
      }
    }

    loadSchedules()
  }, [])

  // Filter configuration
  const filters: FilterConfig[] = [
    {
      key: 'search',
      type: 'search',
      label: 'Search schedules',
      placeholder: 'Search by schedule name, vehicle, driver...'
    },
    {
      key: 'status',
      type: 'select',
      label: 'Status',
      options: [
        { value: 'active', label: 'Active' },
        { value: 'inactive', label: 'Inactive' },
        { value: 'pending', label: 'Pending' },
        { value: 'completed', label: 'Completed' },
        { value: 'cancelled', label: 'Cancelled' }
      ]
    },
    {
      key: 'schedule_type',
      type: 'multiselect',
      label: 'Schedule Type',
      options: [
        { value: 'vehicle', label: 'Vehicle Schedule' },
        { value: 'driver', label: 'Driver Schedule' },
        { value: 'route', label: 'Route Assignment' }
      ]
    },
    {
      key: 'recurring',
      type: 'select',
      label: 'Recurring',
      options: [
        { value: 'true', label: 'Recurring' },
        { value: 'false', label: 'One-time' }
      ]
    },
    {
      key: 'start_date',
      type: 'date',
      label: 'Start Date'
    }
  ]

  // Action configuration
  const actions: ActionConfig[] = [
    {
      action: 'view',
      label: 'View Schedule',
      icon: 'Calendar',
      onClick: (schedule: Schedule) => {
        console.log('View schedule:', schedule.id)
        // Navigate to schedule details
      }
    },
    {
      action: 'edit',
      label: 'Edit Schedule',
      icon: 'Edit',
      onClick: (schedule: Schedule) => {
        console.log('Edit schedule:', schedule.id)
        // Open edit modal or navigate to edit page
      }
    },
    {
      action: 'assign',
      label: 'Auto Assign',
      icon: 'Clock',
      onClick: (schedule: Schedule) => {
        console.log('Auto assign for schedule:', schedule.id)
        // Run auto assignment algorithm
      }
    },
    {
      action: 'delete',
      label: 'Delete Schedule',
      icon: 'Trash2',
      variant: 'destructive',
      onClick: (schedule: Schedule) => {
        if (confirm(`Are you sure you want to delete schedule ${schedule.name}?`)) {
          console.log('Delete schedule:', schedule.id)
          // Call delete API
        }
      }
    }
  ]

  // Card view field configuration
  const cardFields: CardFieldConfig[] = [
    {
      key: 'name',
      label: 'Schedule Name',
      type: 'primary',
      showInHeader: true
    },
    {
      key: 'schedule_type',
      label: 'Type',
      type: 'badge'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'badge',
      showInHeader: true
    },
    {
      key: 'vehicle_id',
      label: 'Vehicle',
      type: 'secondary'
    },
    {
      key: 'driver_id',
      label: 'Driver',
      type: 'secondary'
    },
    {
      key: 'route_id',
      label: 'Route',
      type: 'secondary'
    },
    {
      key: 'start_date',
      label: 'Start Date',
      type: 'date'
    },
    {
      key: 'end_date',
      label: 'End Date',
      type: 'date'
    },
    {
      key: 'description',
      label: 'Time',
      type: 'secondary'
    },
    {
      key: 'shift_hours',
      label: 'Shift Duration',
      type: 'secondary',
      format: (value) => value ? `${value} hours` : 'Not specified'
    }
  ]

  // List view column configuration
  const listColumns: ListColumnConfig[] = [
    {
      key: 'name',
      label: 'Schedule',
      type: 'avatar',
      sortable: true,
      width: 'w-48'
    },
    {
      key: 'schedule_type',
      label: 'Type',
      type: 'badge',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'vehicle_id',
      label: 'Vehicle',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'driver_id',
      label: 'Driver',
      type: 'text',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'route_id',
      label: 'Route',
      type: 'text',
      sortable: true,
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
      key: 'start_date',
      label: 'Start',
      type: 'date',
      sortable: true,
      width: 'w-32'
    },
    {
      key: 'shift_hours',
      label: 'Hours',
      type: 'text',
      sortable: true,
      width: 'w-20'
    }
  ]

  const handleCreateNew = () => {
    console.log('Create new schedule')
    // Navigate to create schedule page or open modal
  }

  const handleRefresh = () => {
    console.log('Refresh schedules')
    // Reload schedules data
    setSchedules(prev => [...prev]) // Force re-render for demo
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
      title="Scheduling Management"
      subtitle="Manage vehicle and driver assignments with automated scheduling"
      entities={schedules}
      loading={loading}
      filters={filters}
      actions={actions}
      cardFields={cardFields}
      listColumns={listColumns}
      onCreateNew={handleCreateNew}
      onRefresh={handleRefresh}
      onFilter={handleFilter}
      onSort={handleSort}
      createButtonText="Create Schedule"
      emptyMessage="No schedules found. Create your first schedule to get started."
    />
  )
}
