# ArkNet Fleet Manager - Unified Page Framework

## Overview

This document describes the unified page framework for ArkNet Fleet Manager, providing consistent UI/UX patterns across all management pages including Vehicles, Drivers, Routes, Timetables, and Scheduling.

## Framework Components

### Core Components

1. **UnifiedPage** - Main page template
2. **FilterBar** - Search and filtering interface  
3. **EntityCard** - Card view for entities
4. **EntityList** - Table/list view for entities
5. **ViewModeToggle** - Switch between card and list views

### Shared Types

All components use unified type definitions in `/types/shared.ts`:

- `BaseEntity` - Base interface for all entities
- `FilterConfig` - Filter configuration
- `ActionConfig` - Action button configuration
- `CardFieldConfig` - Card view field configuration
- `ListColumnConfig` - List view column configuration
- `ViewMode` - Card or list view mode

## Quick Start

### 1. Basic Page Setup

```tsx
import { UnifiedPage } from '@/components/shared/UnifiedPage'
import { FilterConfig, ActionConfig, CardFieldConfig, ListColumnConfig } from '@/types/shared'

export default function MyEntityPage() {
  const [entities, setEntities] = useState([])
  const [loading, setLoading] = useState(true)

  return (
    <UnifiedPage
      title="My Entities"
      subtitle="Manage your entities"
      entities={entities}
      loading={loading}
      filters={filters}
      actions={actions}
      cardFields={cardFields}
      listColumns={listColumns}
      onCreateNew={() => console.log('Create new')}
      onRefresh={() => console.log('Refresh')}
    />
  )
}
```

### 2. Configure Filters

```tsx
const filters: FilterConfig[] = [
  {
    key: 'search',
    type: 'search',
    label: 'Search entities',
    placeholder: 'Search by name, ID, description...'
  },
  {
    key: 'status',
    type: 'select',
    label: 'Status',
    options: [
      { value: 'active', label: 'Active' },
      { value: 'inactive', label: 'Inactive' }
    ]
  },
  {
    key: 'category',
    type: 'multiselect',
    label: 'Category',
    options: [
      { value: 'cat1', label: 'Category 1' },
      { value: 'cat2', label: 'Category 2' }
    ]
  }
]
```

### 3. Configure Actions

```tsx
const actions: ActionConfig[] = [
  {
    action: 'view',
    label: 'View Details',
    icon: 'Eye',
    onClick: (entity) => console.log('View:', entity.id)
  },
  {
    action: 'edit',
    label: 'Edit',
    icon: 'Edit',
    onClick: (entity) => console.log('Edit:', entity.id)
  },
  {
    action: 'delete',
    label: 'Delete',
    icon: 'Trash2',
    variant: 'destructive',
    onClick: (entity) => console.log('Delete:', entity.id)
  }
]
```

### 4. Configure Card View

```tsx
const cardFields: CardFieldConfig[] = [
  {
    key: 'name',
    label: 'Name',
    type: 'primary',
    showInHeader: true
  },
  {
    key: 'description',
    label: 'Description',
    type: 'secondary'
  },
  {
    key: 'status',
    label: 'Status',
    type: 'badge',
    showInHeader: true
  },
  {
    key: 'created_at',
    label: 'Created',
    type: 'date'
  }
]
```

### 5. Configure List View

```tsx
const listColumns: ListColumnConfig[] = [
  {
    key: 'name',
    label: 'Entity',
    type: 'avatar',
    sortable: true,
    width: 'w-48'
  },
  {
    key: 'status',
    label: 'Status',
    type: 'status',
    sortable: true,
    width: 'w-32'
  },
  {
    key: 'created_at',
    label: 'Created',
    type: 'date',
    sortable: true,
    width: 'w-32'
  }
]
```

## Field Types Reference

### Filter Types

- `search` - Global search input
- `select` - Single selection dropdown
- `multiselect` - Multiple selection dropdown  
- `text` - Text input
- `date` - Date picker

### Card Field Types

- `primary` - Primary display field (large text)
- `secondary` - Secondary display field (normal text)
- `badge` - Colored badge/chip
- `status` - Status-specific colored badge
- `date` - Formatted date
- `avatar` - Profile image/avatar
- `link` - Clickable link

### List Column Types

- `text` - Plain text
- `avatar` - Profile image with name
- `status` - Status-specific colored badge
- `badge` - Generic colored badge
- `date` - Formatted date
- `datetime` - Date and time

## Icon Reference

Available icons for actions:

- `Eye` - View/preview
- `Edit` - Edit/modify
- `Trash2` - Delete/remove
- `Car` - Vehicle-related
- `User` - User/driver-related
- `Route` - Route-related
- `Clock` - Time/schedule-related
- `Calendar` - Date/calendar-related

## Styling & Accessibility

### Built-in Features

- **Responsive Design** - Mobile-first responsive layout
- **Accessibility** - WCAG compliant with aria-labels, titles, and keyboard navigation
- **Loading States** - Skeleton loading and spinner animations
- **Empty States** - Customizable empty state messages
- **Hover Effects** - Interactive hover states for better UX

### TailwindCSS Classes

The framework uses consistent TailwindCSS classes:

- **Colors** - Gray palette with blue accents
- **Spacing** - Consistent padding and margins
- **Typography** - Font sizes and weights
- **Borders** - Rounded corners and subtle borders
- **Shadows** - Subtle shadow effects

## Real-time Updates

The framework supports real-time updates via Socket.io:

```tsx
useEffect(() => {
  // Listen for real-time updates
  socket.on('entity_updated', (data) => {
    if (data.entityType === 'vehicle') {
      // Update vehicles list
      setVehicles(prev => prev.map(v => 
        v.id === data.entityId ? { ...v, ...data.changes } : v
      ))
    }
  })

  return () => socket.off('entity_updated')
}, [])
```

## Advanced Customization

### Custom Field Rendering

```tsx
const cardFields: CardFieldConfig[] = [
  {
    key: 'fuel_level',
    label: 'Fuel Level',
    type: 'text',
    render: (value, entity) => (
      <div className="flex items-center gap-2">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div 
            className="bg-blue-600 h-2 rounded-full" 
            style={{ width: `${value}%` }}
          />
        </div>
        <span className="text-sm">{value}%</span>
      </div>
    )
  }
]
```

### Custom Filters

```tsx
const handleFilter = (filters: FilterValue) => {
  // Custom filter logic
  let filtered = entities.filter(entity => {
    // Apply custom filtering logic
    return true
  })
  
  setFilteredEntities(filtered)
}
```

### Custom Sorting

```tsx
const handleSort = (column: string, direction: 'asc' | 'desc') => {
  // Custom sorting logic
  const sorted = [...entities].sort((a, b) => {
    // Apply custom sorting logic
    return 0
  })
  
  setEntities(sorted)
}
```

## Page Examples

Complete examples are available in:

- `/app/vehicles/unified/page.tsx` - Vehicles management
- More examples coming for Drivers, Routes, Timetables, and Scheduling

## Migration Guide

To migrate existing pages to the unified framework:

1. **Identify Entity Structure** - Define your entity interface extending `BaseEntity`
2. **Configure Filters** - Replace existing filter components with `FilterConfig`
3. **Configure Actions** - Replace action buttons with `ActionConfig`
4. **Configure Views** - Define `CardFieldConfig` and `ListColumnConfig`
5. **Replace Page Component** - Use `UnifiedPage` instead of custom page layouts
6. **Test & Refine** - Verify functionality and adjust configurations

## Benefits

- **Consistency** - Uniform UI/UX across all management pages
- **Maintainability** - Single source of truth for common patterns
- **Accessibility** - Built-in accessibility compliance
- **Performance** - Optimized rendering and state management
- **Developer Experience** - Simplified page creation with configuration over code
- **Scalability** - Easy to add new entity types and features

## Support

For questions or issues with the unified framework:

1. Check this documentation first
2. Review example implementations
3. Examine the component source code
4. Create an issue with specific details

## Future Enhancements

Planned framework improvements:

- **Advanced Filtering** - Date ranges, numeric ranges, complex queries
- **Bulk Actions** - Multi-select with bulk operations
- **Column Customization** - User-configurable table columns
- **Export/Import** - CSV/JSON data export and import
- **Audit Trail** - Change history and version tracking
- **Advanced Search** - Full-text search with highlighting
