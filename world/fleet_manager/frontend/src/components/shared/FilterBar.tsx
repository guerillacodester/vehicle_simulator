/**
 * UNIFIED FILTER BAR COMPONENT
 * Reusable filter component for all management pages
 */

'use client'

import { useState, useRef, useEffect } from 'react'
import { 
  Search, 
  Filter, 
  X, 
  ChevronDown,
  RotateCcw
} from 'lucide-react'
import { FilterConfig, FilterState } from '@/types/shared'
import { DynamicFlag, extractCountryCodeFromLabel, removeFlagsFromText } from '@/lib/flags'

// Custom Country Dropdown Component
const CountryDropdown = ({ 
  filter, 
  value, 
  onChange 
}: { 
  filter: FilterConfig; 
  value: string; 
  onChange: (value: string) => void; 
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const selectedOption = filter.options?.find(opt => opt.value === value);

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`
          w-full px-3 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-white 
          focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors
          flex items-center justify-between
          ${isOpen ? 'ring-2 ring-blue-500 border-blue-500' : ''}
        `}
      >
        <span className="flex items-center">
          {selectedOption ? (
            <>
              <DynamicFlag countryCode={extractCountryCodeFromLabel(selectedOption.label)} size={16} className="mr-2" />
              <span>{removeFlagsFromText(selectedOption.label)}</span>
            </>
          ) : (
            <span className="text-gray-400">{filter.placeholder || `Select ${filter.label}`}</span>
          )}
        </span>
        <ChevronDown 
          size={16} 
          className={`text-gray-400 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} 
        />
      </button>

      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-gray-700 border border-gray-600 rounded-md shadow-lg max-h-60 overflow-auto">
          <button
            type="button"
            onClick={() => handleSelect('')}
            className="w-full px-3 py-2 text-left hover:bg-gray-600 focus:bg-gray-600 focus:outline-none text-gray-400 text-sm"
          >
            {filter.placeholder || `Select ${filter.label}`}
          </button>
          {filter.options?.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => handleSelect(option.value)}
              className={`
                w-full px-3 py-2 text-left flex items-center
                hover:bg-gray-600 focus:bg-gray-600 focus:outline-none
                text-white text-sm
                ${value === option.value ? 'bg-blue-600 text-blue-100' : ''}
                transition-colors duration-150
              `}
            >
              <DynamicFlag countryCode={extractCountryCodeFromLabel(option.label)} size={16} className="mr-2" />
              <span>{removeFlagsFromText(option.label)}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

interface FilterBarProps {
  filters: FilterConfig[]
  filterState: FilterState
  onFilterChange: (key: string, value: string | string[]) => void
  onClearFilters: () => void
  searchPlaceholder?: string
  className?: string
}

export function FilterBar({
  filters,
  filterState,
  onFilterChange,
  onClearFilters,
  searchPlaceholder = "Search...",
  className = ""
}: FilterBarProps) {
  const [showFilters, setShowFilters] = useState(false)
  const [searchValue, setSearchValue] = useState(filterState.search as string || '')

  // Count active filters (excluding search)
  const activeFilterCount = Object.keys(filterState).filter(
    key => key !== 'search' && filterState[key] && 
    (Array.isArray(filterState[key]) ? (filterState[key] as string[]).length > 0 : filterState[key] !== '')
  ).length

  const handleSearchChange = (value: string) => {
    setSearchValue(value)
    onFilterChange('search', value)
  }

  const handleClearFilters = () => {
    setSearchValue('')
    onClearFilters()
  }

  return (
    <div className={`flex flex-col gap-3 p-3 bg-gray-800 rounded-lg border border-gray-700 ${className}`}>
      {/* Search and Filter Toggle Row */}
      <div className="flex items-center gap-2">
        {/* Search Input */}
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
          <input
            type="text"
            placeholder={searchPlaceholder}
            value={searchValue}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => handleSearchChange(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
          />
          {searchValue && (
            <button
              onClick={() => handleSearchChange('')}
              className="absolute right-2 top-1/2 transform -translate-y-1/2 h-5 w-5 p-0 text-gray-400 hover:text-gray-200 transition-colors"
              title="Clear search"
              aria-label="Clear search"
            >
              <X className="h-3 w-3" />
            </button>
          )}
        </div>

        {/* Filter Toggle Button */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-3 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-white hover:bg-gray-600 transition-colors"
        >
          <Filter className="h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="ml-1 px-1.5 py-0.5 text-xs bg-blue-600 text-white rounded-full min-w-[1.25rem] text-center">
              {activeFilterCount}
            </span>
          )}
          <ChevronDown className={`h-4 w-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
        </button>

        {/* Clear Filters Button */}
        {(activeFilterCount > 0 || searchValue) && (
          <button
            onClick={handleClearFilters}
            className="flex items-center gap-1 px-3 py-2 text-sm text-gray-400 hover:text-white transition-colors"
            title="Clear all filters"
          >
            <RotateCcw className="h-4 w-4" />
            Clear
          </button>
        )}
      </div>

      {/* Filter Controls */}
      {showFilters && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 pt-3 border-t border-gray-600">
          {filters.filter(filter => filter.type !== 'search').map((filter) => (
            <div key={filter.key} className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-400 uppercase tracking-wide">
                {filter.label}
              </label>
              
              {filter.type === 'select' && (
                <>
                  {filter.key === 'country' || filter.label.toLowerCase().includes('country') ? (
                    <CountryDropdown
                      filter={filter}
                      value={filterState[filter.key] as string || ''}
                      onChange={(value) => onFilterChange(filter.key, value)}
                    />
                  ) : (
                    <select
                      value={filterState[filter.key] as string || ''}
                      onChange={(e: React.ChangeEvent<HTMLSelectElement>) => onFilterChange(filter.key, e.target.value)}
                      className="w-full px-3 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                      title={`Select ${filter.label}`}
                      aria-label={`Select ${filter.label}`}
                    >
                      <option value="">{filter.placeholder || `Select ${filter.label}`}</option>
                      {filter.options?.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  )}
                </>
              )}

              {filter.type === 'text' && (
                <input
                  type="text"
                  placeholder={filter.placeholder || `Enter ${filter.label}`}
                  value={filterState[filter.key] as string || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => onFilterChange(filter.key, e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  title={`Enter ${filter.label}`}
                  aria-label={`Enter ${filter.label}`}
                />
              )}

              {filter.type === 'date' && (
                <input
                  type="date"
                  value={filterState[filter.key] as string || ''}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => onFilterChange(filter.key, e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-600 rounded-md bg-gray-700 text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-colors"
                  title={`Select ${filter.label}`}
                  aria-label={`Select ${filter.label}`}
                />
              )}

              {/* Clear individual filter */}
              {filterState[filter.key] && (
                <button
                  onClick={() => onFilterChange(filter.key, '')}
                  className="self-start text-xs text-gray-400 hover:text-gray-200 h-6 px-2"
                >
                  Clear
                </button>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Active Filter Tags */}
      {activeFilterCount > 0 && (
        <div className="flex flex-wrap gap-2 pt-2 border-t">
          <span className="text-sm text-gray-300 font-medium">Active filters:</span>
          {Object.entries(filterState).map(([key, value]) => {
            if (key === 'search' || !value || (Array.isArray(value) && value.length === 0)) return null
            
            const filter = filters.find(f => f.key === key)
            if (!filter) return null

            const displayValue = Array.isArray(value) ? value.join(', ') : value
            const option = filter.options?.find(opt => opt.value === value)
            const displayLabel = option ? option.label : displayValue

            return (
              <span
                key={key}
                className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 text-gray-700 rounded-md text-sm"
              >
                <span>{filter.label}: {displayLabel}</span>
                <button
                  onClick={() => onFilterChange(key, '')}
                  className="h-4 w-4 p-0 hover:bg-gray-200 rounded"
                  title={`Remove ${filter.label} filter`}
                  aria-label={`Remove ${filter.label} filter`}
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )
          })}
        </div>
      )}
    </div>
  )
}
