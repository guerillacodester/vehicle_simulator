/**
 * UNIFIED ENTITY LIST COMPONENT
 * Table-style list view for all management pages
 */

'use client'

import { 
  Eye, 
  Edit, 
  Trash2, 
  MoreHorizontal,
  Car,
  User,
  Route,
  Clock,
  Calendar,
  ArrowUpDown,
  ArrowUp,
  ArrowDown
} from 'lucide-react'
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "../ui/avatar"
import { ListColumnConfig, ActionConfig, BaseEntity } from '@/types/shared'

interface EntityListProps {
  entities: BaseEntity[]
  columns: ListColumnConfig[]
  actions: ActionConfig[]
  loading?: boolean
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  emptyMessage?: string
}

// Helper function to render icon by name
const renderIcon = (iconName: string, className: string = "h-4 w-4") => {
  switch (iconName) {
    case 'Eye': return <Eye className={className} />
    case 'Edit': return <Edit className={className} />
    case 'Trash2': return <Trash2 className={className} />
    case 'Car': return <Car className={className} />
    case 'User': return <User className={className} />
    case 'Route': return <Route className={className} />
    case 'Clock': return <Clock className={className} />
    case 'Calendar': return <Calendar className={className} />
    default: return null
  }
}

// Helper function to render cell content
const renderCellContent = (entity: BaseEntity, column: ListColumnConfig) => {
  const value = entity[column.key]
  
  switch (column.type) {
    case 'avatar':
      return (
        <div className="flex items-center gap-3">
          <Avatar className="h-8 w-8">
            <AvatarImage src={entity.image_url} alt={entity.name || entity.id} />
            <AvatarFallback className="text-xs">
              {entity.name?.charAt(0)?.toUpperCase() || entity.id?.charAt(0)?.toUpperCase()}
            </AvatarFallback>
          </Avatar>
          <div>
            <div className="font-medium text-white">{entity.name || entity.id}</div>
            {entity.description && (
              <div className="text-sm text-gray-500">{entity.description}</div>
            )}
          </div>
        </div>
      )
      
    case 'status':
      if (!value) return <span className="text-gray-400">-</span>
      const statusColors = {
        active: 'bg-green-100 text-green-800',
        inactive: 'bg-gray-100 text-gray-800', 
        maintenance: 'bg-yellow-100 text-yellow-800',
        out_of_service: 'bg-red-100 text-red-800',
        available: 'bg-blue-100 text-blue-800',
        unavailable: 'bg-gray-100 text-gray-800',
        online: 'bg-green-100 text-green-800',
        offline: 'bg-red-100 text-red-800'
      }
      return (
        <Badge 
          className={`${statusColors[value as keyof typeof statusColors] || 'bg-gray-100 text-gray-800'} hover:bg-opacity-80`}
        >
          {String(value).replace('_', ' ')}
        </Badge>
      )
      
    case 'badge':
      if (!value) return <span className="text-gray-400">-</span>
      return (
        <Badge variant="outline">
          {String(value)}
        </Badge>
      )
      
    case 'date':
      if (!value) return <span className="text-gray-400">-</span>
      return (
        <span className="text-white">
          {new Date(String(value)).toLocaleDateString()}
        </span>
      )
      
    case 'datetime':
      if (!value) return <span className="text-gray-400">-</span>
      return (
        <div>
          <div className="text-white">
            {new Date(String(value)).toLocaleDateString()}
          </div>
          <div className="text-sm text-gray-500">
            {new Date(String(value)).toLocaleTimeString()}
          </div>
        </div>
      )
      
    case 'text':
    default:
      if (!value) return <span className="text-gray-400">-</span>
      return <span className="text-white">{String(value)}</span>
  }
}

export function EntityList({
  entities,
  columns,
  actions,
  loading = false,
  onSort,
  sortColumn,
  sortDirection,
  emptyMessage = "No items found"
}: EntityListProps) {
  if (loading) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-8 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-400">Loading...</p>
        </div>
      </div>
    )
  }

  if (entities.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg border border-gray-700">
        <div className="p-8 text-center">
          <p className="text-gray-400">{emptyMessage}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-800 rounded-lg border border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-700 border-b border-gray-600">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider ${
                    column.sortable ? 'cursor-pointer hover:bg-gray-700' : ''
                  } ${column.width || ''}`}
                  onClick={() => {
                    if (column.sortable && onSort) {
                      const direction = sortColumn === column.key && sortDirection === 'asc' ? 'desc' : 'asc'
                      onSort(column.key, direction)
                    }
                  }}
                >
                  <div className="flex items-center gap-2">
                    {column.label}
                    {column.sortable && (
                      <div className="flex flex-col">
                        {sortColumn === column.key ? (
                          sortDirection === 'asc' ? (
                            <ArrowUp className="h-3 w-3" />
                          ) : (
                            <ArrowDown className="h-3 w-3" />
                          )
                        ) : (
                          <ArrowUpDown className="h-3 w-3 text-gray-400" />
                        )}
                      </div>
                    )}
                  </div>
                </th>
              ))}
              {actions.length > 0 && (
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider w-20">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody className="bg-gray-800 divide-y divide-gray-700">
            {entities.map((entity, index) => (
              <tr 
                key={entity.id || index}
                className="hover:bg-gray-700 transition-colors"
              >
                {columns.map((column) => (
                  <td key={column.key} className={`px-6 py-4 whitespace-nowrap ${column.width || ''}`}>
                    {renderCellContent(entity, column)}
                  </td>
                ))}
                
                {actions.length > 0 && (
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="relative group">
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0"
                        title="More actions"
                        aria-label="More actions"
                      >
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                      
                      {/* Actions Dropdown */}
                      <div className="absolute right-0 top-full mt-1 w-36 bg-gray-700 border border-gray-600 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
                        {actions.map((action) => (
                          <button
                            key={action.action}
                            onClick={() => action.onClick(entity)}
                            className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-600 first:rounded-t-lg last:rounded-b-lg transition-colors ${
                              action.variant === 'destructive' ? 'text-red-400 hover:bg-red-900' : 'text-gray-200'
                            }`}
                            title={action.label}
                            aria-label={action.label}
                          >
                            {renderIcon(action.icon)}
                            {action.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
