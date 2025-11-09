# Map Components Architecture

This directory contains a refactored, well-architected Leaflet map implementation following React best practices.

## Component Structure

### Main Component
- **LeafletMapClient.tsx** - Main orchestration component that composes hooks and manages state

### Custom Hooks (Separation of Concerns)
- **useLeafletLoader.ts** - Handles dynamic CDN loading of Leaflet library
- **useLeafletMap.ts** - Manages map initialization and lifecycle
- **usePOILayer.ts** - Manages POI (Point of Interest) markers and route stops

### Type Definitions
- **leafletTypes.ts** - Complete TypeScript definitions for Leaflet API
  - Proper type safety without `any`
  - Extended interfaces for all Leaflet objects
  - Type guards and helper functions

### Constants
- **mapConstants.ts** - Centralized configuration
  - Z-index layering (prevents stacking issues)
  - Map configuration (tiles, zoom levels, etc.)
  - Animation timing constants

### UI Components
- **MapControlPanel.tsx** - Slide-in control panel with route search

## Design Principles Applied

### 1. Separation of Concerns
Each hook has a single responsibility:
- Loading → `useLeafletLoader`
- Map init → `useLeafletMap`
- POI rendering → `usePOILayer`

### 2. Type Safety
- No `any` types in production code
- Proper TypeScript interfaces for all Leaflet objects
- Type guards for safe global access

### 3. Proper React Patterns
- Refs used correctly (not accessed during render)
- Effects properly scoped with correct dependencies
- Callbacks memoized to prevent unnecessary re-renders

### 4. Z-Index Management
Centralized z-index constants prevent stacking conflicts:
```typescript
MAP_Z_INDEX = {
  MAP_BASE: 1,
  MAP_TILES: 400,
  LEAFLET_CONTROLS: 1000,
  HAMBURGER_BUTTON: 1001,
  CONTROL_PANEL: 1002,
}
```

### 5. Configuration Management
All magic numbers extracted to constants:
- Tile URLs
- Zoom limits
- Animation timing
- Default coordinates

## Usage

```tsx
import LeafletMapClient from './LeafletMapClient';

<LeafletMapClient 
  center={[13.2, -59.55]} 
  zoom={10} 
  height="75vh" 
/>
```

## Key Features

✅ **Scale control at top-right** - Fixed position, edge-to-edge, always visible  
✅ **Proper z-index stacking** - No flickering or overlapping issues  
✅ **Slide-in control panel** - Smooth animations, doesn't hide hamburger  
✅ **Edge-to-edge controls** - No gaps between map edge and controls  
✅ **Persistent hamburger** - Always accessible, no border/outline  
✅ **Route POI markers** - Dynamic loading and bounds fitting  
✅ **Type-safe** - Full TypeScript coverage  
✅ **Testable** - Clean hooks can be unit tested  
✅ **Maintainable** - Clear separation, easy to extend

## Extension Points

To add new features:
1. **New map layer** - Create a new `use[Feature]Layer` hook
2. **New control** - Add to `mapConstants` and create component
3. **New tile provider** - Update `MAP_CONFIG.TILE_URL`
4. **New interaction** - Add handler in `LeafletMapClient`

## CSS Classes

- `.map-control-panel` - Control panel container
- `.map-control-panel.open` - Active state
- `.leaflet-control-scale` - Scale control styling
- `.route-item-btn` - Route list item buttons

## Performance Notes

- Leaflet loaded from CDN (cached across page loads)
- Map instance reused (not recreated on prop changes)
- Markers managed via layer groups (efficient updates)
- Effects properly scoped (minimal re-renders)
