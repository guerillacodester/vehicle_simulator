/**
 * UNIFIED PAGE TEMPLATE
 * Template for all management pages with consistent UI/UX
 */

'use client'

import { useState, useEffect } from 'react'
import { FilterBar } from './FilterBar'
import { EntityCard } from './EntityCard'
import { EntityList } from './EntityList'
import { ViewModeToggle } from './ViewModeToggle'
import { Button } from "@/components/ui/button"
import { Plus, RefreshCw } from 'lucide-react'
import { 
  BaseEntity, 
  ViewMode, 
  FilterConfig, 
  ActionConfig, 
  CardFieldConfig, 
  ListColumnConfig,
  FilterValue 
} from '@/types/shared'

interface UnifiedPageProps {
  // Page configuration
  title: string
  subtitle?: string
  
  // Data
  entities: BaseEntity[]
  loading?: boolean
  
  // View configuration
  filters: FilterConfig[]
  actions: ActionConfig[]
  cardFields: CardFieldConfig[]
  listColumns: ListColumnConfig[]
  
  // Callbacks
  onCreateNew?: () => void
  onRefresh?: () => void
  onFilter?: (filters: FilterValue) => void
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  
  // Optional customization
  emptyMessage?: string
  createButtonText?: string
  showCreateButton?: boolean
  showRefreshButton?: boolean
  className?: string
}

export function UnifiedPage({
  title,
  subtitle,
  entities,
  loading = false,
  filters,
  actions,
  cardFields,
  listColumns,
  onCreateNew,
  onRefresh,
  onFilter,
  onSort,
  emptyMessage,
  createButtonText = "Create New",
  showCreateButton = true,
  showRefreshButton = true,
  className = ''
}: UnifiedPageProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('card')
  const [currentFilters, setCurrentFilters] = useState<FilterValue>({})
  const [sortColumn, setSortColumn] = useState<string>('')
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [filteredEntities, setFilteredEntities] = useState<BaseEntity[]>(entities)

  // Filter entities when filters or entities change
  useEffect(() => {
    let filtered = [...entities]

    // Apply filters
    Object.entries(currentFilters).forEach(([key, value]) => {
      if (value && value !== '') {
        if (key === 'search') {
          // Global search across available entity fields
          const searchTerm = String(value).toLowerCase()
          filtered = filtered.filter(entity => {
            // Search in common fields that might exist
            const searchableFields = [
              entity.name,
              entity.description, 
              entity.id,
              entity.reg_code, // for vehicles
              entity.license_no, // for drivers
              entity.route_name,
              entity.route_number,
              entity.origin,
              entity.destination
            ]
            
            return searchableFields.some(field => 
              field && String(field).toLowerCase().includes(searchTerm)
            )
          })
        } else if (Array.isArray(value)) {
          // Multi-select filter
          if (value.length > 0) {
            filtered = filtered.filter(entity => 
              value.includes((entity as any)[key])
            )
          }
        } else {
          // Single value filter
          filtered = filtered.filter(entity => 
            (entity as any)[key] === value
          )
        }
      }
    })

    // Apply sorting
    if (sortColumn) {
      filtered.sort((a, b) => {
        const aVal = (a as any)[sortColumn]
        const bVal = (b as any)[sortColumn]
        
        if (aVal === null || aVal === undefined) return 1
        if (bVal === null || bVal === undefined) return -1
        
        let result = 0
        if (typeof aVal === 'string' && typeof bVal === 'string') {
          result = aVal.localeCompare(bVal)
        } else {
          result = String(aVal).localeCompare(String(bVal))
        }
        
        return sortDirection === 'desc' ? -result : result
      })
    }

    setFilteredEntities(filtered)
  }, [entities, currentFilters, sortColumn, sortDirection])

  const handleFilter = (newFilters: FilterValue) => {
    setCurrentFilters(newFilters)
    onFilter?.(newFilters)
  }

  const handleSort = (column: string, direction: 'asc' | 'desc') => {
    setSortColumn(column)
    setSortDirection(direction)
    onSort?.(column, direction)
  }

  const handleRefresh = () => {
    setCurrentFilters({})
    setSortColumn('')
    setSortDirection('asc')
    onRefresh?.()
  }

  return (
    <div className={`min-h-screen bg-gray-900 text-white space-y-6 p-6 ${className}`}>
      {/* Page Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">{title}</h1>
          {subtitle && (
            <p className="mt-2 text-gray-300">{subtitle}</p>
          )}
        </div>
        
        <div className="flex items-center gap-3">
          {showRefreshButton && (
            <Button
              variant="outline"
              onClick={handleRefresh}
              disabled={loading}
              title="Refresh data"
              aria-label="Refresh data"
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          )}
          
          {showCreateButton && onCreateNew && (
            <Button
              onClick={onCreateNew}
              title={createButtonText}
              aria-label={createButtonText}
            >
              <Plus className="h-4 w-4 mr-2" />
              {createButtonText}
            </Button>
          )}
        </div>
      </div>

      {/* Filter Bar */}
      <FilterBar
        filters={filters}
        filterState={currentFilters}
        onFilterChange={(key, value) => {
          const newFilters = { ...currentFilters, [key]: value }
          handleFilter(newFilters)
        }}
        onClearFilters={() => handleFilter({})}
      />

      {/* View Controls */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-300">
            {loading ? 'Loading...' : `${filteredEntities.length} items`}
          </span>
        </div>
        
        <ViewModeToggle 
          viewMode={viewMode} 
          onViewModeChange={setViewMode}
        />
      </div>

      {/* Content Area */}
      <div className="min-h-[400px]">
        {viewMode === 'card' ? (
          loading ? (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="h-48 bg-gray-800 rounded-lg animate-pulse" />
              ))}
            </div>
          ) : filteredEntities.length === 0 ? (
            <div className="text-center py-16">
              <p className="text-gray-400">{emptyMessage || 'No items found'}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-3">
              {filteredEntities.map((entity) => (
                <EntityCard
                  key={entity.id}
                  entity={entity}
                  fields={cardFields}
                  actions={actions}
                />
              ))}
            </div>
          )
        ) : (
          <EntityList
            entities={filteredEntities}
            columns={listColumns}
            actions={actions}
            loading={loading}
            onSort={handleSort}
            sortColumn={sortColumn}
            sortDirection={sortDirection}
            emptyMessage={emptyMessage}
          />
        )}
      </div>
    </div>
  )
}
