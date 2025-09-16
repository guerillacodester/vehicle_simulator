/**
 * UNIFIED ENTITY CARD COMPONENT
 * Reusable card component for all management pages
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
  Calendar
} from 'lucide-react'
import { CardFieldConfig, ActionConfig } from '@/types/shared'

interface EntityCardProps {
  entity: any
  fields: CardFieldConfig[]
  actions: ActionConfig[]
  className?: string
}

const getFieldIcon = (type: string) => {
  switch (type) {
    case 'vehicle': return Car
    case 'driver': return User
    case 'route': return Route
    case 'schedule': return Calendar
    default: return Clock
  }
}

const StatusBadge = ({ status, type }: { status: string; type?: string }) => {
  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'available':
      case 'active':
      case 'scheduled':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'maintenance':
      case 'on_leave':
      case 'inactive':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'retired':
      case 'cancelled':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'completed':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      default:
        return 'bg-gray-700 text-gray-200 border-gray-600'
    }
  }

  return (
    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getStatusColor(status)}`}>
      {status}
    </span>
  )
}

const Avatar = ({ src, name, size = 'sm' }: { src?: string; name: string; size?: 'sm' | 'md' | 'lg' }) => {
  const sizeClasses = {
    sm: 'h-8 w-8 text-xs',
    md: 'h-10 w-10 text-sm',
    lg: 'h-12 w-12 text-base'
  }

  const initials = name
    .split(' ')
    .map(word => word.charAt(0))
    .join('')
    .substring(0, 2)
    .toUpperCase()

  if (src) {
    return (
      <img
        src={src}
        alt={name}
        className={`${sizeClasses[size]} rounded-full object-cover border border-gray-600`}
      />
    )
  }

  return (
    <div className={`${sizeClasses[size]} rounded-full bg-blue-500 text-white flex items-center justify-center font-medium border border-gray-600`}>
      {initials}
    </div>
  )
}

const renderFieldValue = (field: CardFieldConfig, entity: any) => {
  const value = entity[field.key]

  if (field.render) {
    return field.render(value, entity)
  }

  switch (field.type) {
    case 'badge':
      return <StatusBadge status={value} />
    
    case 'avatar':
      return <Avatar src={entity.photo_url || entity.avatar} name={value} />
    
    case 'date':
      return value ? new Date(value).toLocaleDateString() : '-'
    
    case 'status':
      return <StatusBadge status={value} />
    
    case 'link':
      return (
        <a href={value} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer">
          View
        </a>
      )
    
    default:
      return value || '-'
  }
}

export function EntityCard({ entity, fields, actions, className = '' }: EntityCardProps) {
  const primaryField = fields.find(f => f.primary)
  const secondaryFields = fields.filter(f => !f.primary)

  return (
    <div className={`
      bg-gray-800 rounded-lg border border-gray-700 shadow-sm p-3
      card-3d relative overflow-hidden
      group cursor-pointer
      ${className}
    `}>
      <div className="card-content relative z-10">
        {/* Header with Primary Field */}
        {primaryField && (
          <div className="flex items-start justify-between mb-2">
            <div className="flex items-center gap-2">
            {primaryField.type === 'avatar' && (
              <Avatar 
                src={entity.photo_url || entity.avatar} 
                name={entity[primaryField.key]} 
                size="sm" 
              />
            )}
            <div>
              <h3 className="text-sm font-semibold text-white leading-tight">
                {renderFieldValue(primaryField, entity)}
              </h3>
              {entity.subtitle && (
                <p className="text-xs text-gray-400 mt-1">{entity.subtitle}</p>
              )}
            </div>
          </div>
          
          {/* Actions Dropdown */}
          <div className="relative group">
            <button 
              className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-50 transition-colors"
              title="More actions"
              aria-label="More actions"
            >
              <MoreHorizontal className="h-4 w-4" />
            </button>
            
            {/* Actions Menu */}
            <div className="absolute right-0 top-full mt-1 w-36 bg-gray-700 border border-gray-600 rounded-lg shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-10">
              {actions.map((action) => {
                return (
                  <button
                    key={action.action}
                    onClick={() => action.onClick(entity)}
                    className={`w-full flex items-center gap-2 px-3 py-2 text-sm text-left hover:bg-gray-50 first:rounded-t-lg last:rounded-b-lg transition-colors ${
                      action.variant === 'destructive' ? 'text-red-600 hover:bg-red-50' : 'text-gray-700'
                    }`}
                  >
                    {action.icon === 'Eye' && <Eye className="h-4 w-4" />}
                    {action.icon === 'Edit' && <Edit className="h-4 w-4" />}
                    {action.icon === 'Trash2' && <Trash2 className="h-4 w-4" />}
                    {action.icon === 'Car' && <Car className="h-4 w-4" />}
                    {action.icon === 'User' && <User className="h-4 w-4" />}
                    {action.icon === 'Route' && <Route className="h-4 w-4" />}
                    {action.icon === 'Clock' && <Clock className="h-4 w-4" />}
                    {action.icon === 'Calendar' && <Calendar className="h-4 w-4" />}
                    {action.label}
                  </button>
                )
              })}
            </div>
          </div>
        </div>
      )}

      {/* Secondary Fields Grid */}
      <div className="grid grid-cols-1 gap-1">
        {secondaryFields.map((field) => (
          <div key={field.key} className="flex items-center justify-between">
            <span className="text-xs font-medium text-gray-500 transition-colors duration-300 group-hover:text-gray-400">
              {field.label}:
            </span>
            <div className="text-xs text-white transition-colors duration-300 group-hover:text-blue-100">
              {renderFieldValue(field, entity)}
            </div>
          </div>
        ))}
      </div>

      {/* Footer Actions (Alternative to Dropdown) */}
      <div className="flex items-center justify-between mt-2 pt-2 border-t border-gray-700 transform transition-all duration-300 group-hover:translate-z-1 group-hover:border-blue-400/30">
        <div className="flex items-center gap-1">
          {actions.slice(0, 2).map((action) => {
            return (
              <button
                key={action.action}
                onClick={() => action.onClick(entity)}
                className={`flex items-center gap-1 px-2 py-1 text-xs font-medium rounded-md transition-colors ${
                  action.variant === 'destructive' 
                    ? 'text-red-600 bg-red-50 hover:bg-red-100' 
                    : 'text-gray-600 bg-gray-50 hover:bg-gray-100'
                }`}
              >
                {action.icon === 'Eye' && <Eye className="h-3 w-3" />}
                {action.icon === 'Edit' && <Edit className="h-3 w-3" />}
                {action.icon === 'Trash2' && <Trash2 className="h-3 w-3" />}
                {action.icon === 'Car' && <Car className="h-3 w-3" />}
                {action.icon === 'User' && <User className="h-3 w-3" />}
                {action.icon === 'Route' && <Route className="h-3 w-3" />}
                {action.icon === 'Clock' && <Clock className="h-3 w-3" />}
                {action.icon === 'Calendar' && <Calendar className="h-3 w-3" />}
                {action.label}
              </button>
            )
          })}
        </div>
        
        {/* Entity Type Badge */}
        <span className="text-xs text-gray-400 font-medium uppercase tracking-wide">
          {entity.entity_type || 'Entity'}
        </span>
      </div>
      </div>
    </div>
  )
}
