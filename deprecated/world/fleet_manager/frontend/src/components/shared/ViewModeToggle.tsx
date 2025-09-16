/**
 * VIEW MODE TOGGLE COMPONENT
 * Switches between card and list views
 */

'use client'

import { Grid3X3, List } from 'lucide-react'
import { Button } from "@/components/ui/button"
import { ViewMode } from '@/types/shared'

interface ViewModeToggleProps {
  viewMode: ViewMode
  onViewModeChange: (mode: ViewMode) => void
  className?: string
}

export function ViewModeToggle({ 
  viewMode, 
  onViewModeChange, 
  className = '' 
}: ViewModeToggleProps) {
  return (
    <div className={`flex items-center rounded-lg border border-gray-200 p-1 ${className}`}>
      <Button
        variant={viewMode === 'card' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onViewModeChange('card')}
        className="h-8 w-8 p-0"
        title="Card view"
        aria-label="Switch to card view"
      >
        <Grid3X3 className="h-4 w-4" />
      </Button>
      
      <Button
        variant={viewMode === 'list' ? 'default' : 'ghost'}
        size="sm"
        onClick={() => onViewModeChange('list')}
        className="h-8 w-8 p-0"
        title="List view"
        aria-label="Switch to list view"
      >
        <List className="h-4 w-4" />
      </Button>
    </div>
  )
}
