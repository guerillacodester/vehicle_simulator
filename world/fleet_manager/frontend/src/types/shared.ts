/**
 * SHARED TYPES FOR ARKNET FLEET MANAGER
 * Unified type definitions for all management pages
 */

// Base entity interface that all entities extend
export interface BaseEntity {
  id: string
  created_at: string
  updated_at: string
  name?: string
  description?: string
  image_url?: string
  status?: string
  entity_type?: string
  [key: string]: any  // Allow additional properties
}

// View modes for all pages
export type ViewMode = 'card' | 'list'

// Action types for entity interactions
export type EntityAction = 'view' | 'edit' | 'delete' | 'assign' | 'unassign'

// Filter configuration for each page
export interface FilterConfig {
  key: string
  label: string
  type: 'select' | 'text' | 'date' | 'multiselect' | 'search'
  options?: Array<{ value: string; label: string }>
  placeholder?: string
}

// Generic filter state
export interface FilterState {
  [key: string]: string | string[]
}

// Alias for backward compatibility and clarity
export type FilterValue = FilterState

// Entity action configuration
export interface ActionConfig {
  action: EntityAction
  label: string
  icon: string  // Icon name as string (e.g., 'Eye', 'Edit', 'Trash2')
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost'
  onClick: (entity: any) => void
}

// Page configuration
export interface PageConfig {
  title: string
  subtitle?: string
  filters: FilterConfig[]
  actions: ActionConfig[]
  cardFields: CardFieldConfig[]
  listColumns: ListColumnConfig[]
}

// Card field configuration
export interface CardFieldConfig {
  key: string
  label: string
  type: 'text' | 'badge' | 'avatar' | 'date' | 'status' | 'link' | 'primary' | 'secondary'
  primary?: boolean
  showInHeader?: boolean
  format?: (value: any) => string
  render?: (value: any, entity: any) => React.ReactNode
}

// List column configuration
export interface ListColumnConfig {
  key: string
  label: string
  type?: 'text' | 'avatar' | 'status' | 'badge' | 'date' | 'datetime'
  sortable?: boolean
  width?: string
  render?: (value: any, entity: any) => React.ReactNode
}

// Socket.IO event types for real-time updates
export interface SocketEvent {
  type: 'entity_updated' | 'entity_created' | 'entity_deleted' | 'assignment_changed'
  entityType: 'vehicle' | 'driver' | 'route' | 'timetable' | 'schedule'
  entityId: string
  data: any
}

// Specific entity types
export interface Vehicle extends BaseEntity {
  vehicle_id: string
  reg_code: string
  country_id: string
  home_depot_id?: string
  preferred_route_id?: string
  assigned_driver_id?: string
  status: 'available' | 'maintenance' | 'retired'
  profile_id?: string
  notes?: string
  // Extended fields
  country_name?: string
  depot_name?: string
  route_name?: string
  driver_name?: string
}

export interface Driver extends BaseEntity {
  driver_id: string
  first_name: string
  last_name: string
  country_id: string
  employment_status: 'active' | 'inactive' | 'on_leave'
  assigned_vehicle_id?: string
  photo_url?: string
  license_number?: string
  phone?: string
  email?: string
  // Extended fields
  country_name?: string
  vehicle_reg?: string
  full_name?: string
}

export interface Route extends BaseEntity {
  route_id: string
  route_name: string
  country_id: string
  service_id?: string
  trip_id?: string
  geojson_data?: any
  // Extended fields
  country_name?: string
  trip_count?: number
  stop_count?: number
}

export interface Timetable extends BaseEntity {
  timetable_id: string
  service_id: string
  route_id?: string
  block_id?: string
  trip_id?: string
  stop_id?: string
  departure_time?: string
  arrival_time?: string
  // Extended fields
  route_name?: string
  stop_name?: string
}

export interface Schedule extends BaseEntity {
  schedule_id: string
  vehicle_id?: string
  driver_id?: string
  service_id?: string
  block_id?: string
  start_time: string
  end_time: string
  status: 'scheduled' | 'active' | 'completed' | 'cancelled'
  // Extended fields
  vehicle_reg?: string
  driver_name?: string
  service_name?: string
}
