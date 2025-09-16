/**
 * VEHICLES CLIENT COMPONENT
 * Comprehensive vehicle management with card/list views, filtering, and actions
 */

'use client'

import { useState, useEffect, useMemo } from 'react'
import { 
  Search, 
  Filter, 
  Grid3x3, 
  List, 
  Plus, 
  Eye, 
  Edit, 
  Trash2,
  Car,
  ChevronDown,
  X,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  XCircle
} from 'lucide-react'
import { dataProvider } from '@/infrastructure/data-provider'

// Types - Real API structure
interface Vehicle {
  vehicle_id: string
  reg_code: string
  country_id: string
  home_depot_id?: string | null
  preferred_route_id?: string | null
  status: 'available' | 'maintenance' | 'retired'
  profile_id?: string | null
  notes?: string | null
  created_at: string
  updated_at: string
  // Extended fields (from joins/lookups)
  country_name?: string
  depot_name?: string
  route_name?: string
}

interface VehicleFilters {
  search: string
  country: string
  depot: string
  route: string
  status: string
}

type ViewMode = 'card' | 'list'

const VEHICLES_PER_PAGE = 50
const INITIAL_FILTERS: VehicleFilters = {
  search: '',
  country: '',
  depot: '',
  route: '',
  status: ''
}

export default function VehiclesClient() {
  console.log('🔥 COMPONENT MOUNTING!')
  
  // State management
  const [vehicles, setVehicles] = useState<Vehicle[]>([])
  const [filteredVehicles, setFilteredVehicles] = useState<Vehicle[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<ViewMode>('card')
  const [filters, setFilters] = useState<VehicleFilters>(INITIAL_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)

  // SIMPLE WORKING APPROACH - based on successful test
  useEffect(() => {
    console.log('� VEHICLES CLIENT MOUNTED')
    
    const loadEverything = async () => {
      try {
        console.log('� Making direct fetch to vehicles API...')
        const vehiclesResponse = await fetch('http://localhost:8000/api/v1/vehicles/')
        const vehiclesData = await vehiclesResponse.json()
        console.log('📦 RECEIVED VEHICLES:', vehiclesData.length)
        
        // Set vehicles immediately - this is what works!
        setVehicles(vehiclesData)
        setFilteredVehicles(vehiclesData)
        console.log('✅ VEHICLES STATE UPDATED:', vehiclesData.length)
        
        // ALSO: Set global country selection if available
        if (typeof window !== 'undefined') {
          const savedCountry = localStorage.getItem('arknet-selected-country')
          if (savedCountry) {
            try {
              const country = JSON.parse(savedCountry)
              console.log('🌍 Setting global country after vehicles loaded:', country.name)
              setFilters(prev => ({ ...prev, country: country.country_id }))
            } catch (error) {
              console.error('Failed to parse saved country:', error)
            }
          }
        }
        
        // Load filter options
        const [countriesRes, depotsRes] = await Promise.all([
          fetch('http://localhost:8000/api/v1/countries/'),
          fetch('http://localhost:8000/api/v1/depots/')
        ])
        
        const countries = await countriesRes.json()
        const depots = await depotsRes.json()
        
        setFilterOptions(prev => ({
          ...prev,
          countries: countries.map((c: any) => ({ id: c.country_id, name: c.name })),
          depots: depots.map((d: any) => ({ id: d.depot_id, name: d.name }))
        }))
        
        console.log('✅ FILTER OPTIONS LOADED')
        
      } catch (error) {
        console.error('❌ ERROR LOADING DATA:', error)
        setError('Failed to load data')
      } finally {
        setIsLoading(false)
        console.log('🏁 LOADING COMPLETE')
      }
    }

    loadEverything()
  }, [])

  // DISABLED - This was overriding our working vehicles!
  // useEffect(() => {
  //   const initializeData = async () => {
  //     try {
  //       await loadVehicles()
  //     } catch (error) {
  //       console.error('Failed to load vehicles:', error)
  //     }
  //   }
  //   
  //   initializeData()
  // }, [])

  // Set global country selection
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedCountry = localStorage.getItem('arknet-selected-country')
      if (savedCountry) {
        try {
          const country = JSON.parse(savedCountry)
          console.log('Setting global country:', country)
          setFilters(prev => ({ ...prev, country: country.country_id }))
        } catch (error) {
          console.error('Failed to parse saved country:', error)
        }
      }
    }
  }, [])

  // Listen for changes to the global country selection
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'arknet-selected-country' && e.newValue) {
        try {
          const country = JSON.parse(e.newValue)
          setFilters(prev => ({ ...prev, country: country.country_id }))
        } catch (error) {
          console.error('Failed to parse country from storage event:', error)
        }
      }
    }

    const handleCountryChange = (e: CustomEvent) => {
      if (e.detail && e.detail.country_id) {
        setFilters(prev => ({ ...prev, country: e.detail.country_id }))
      }
    }

    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleStorageChange)
      window.addEventListener('arknet-country-changed', handleCountryChange as EventListener)
      return () => {
        window.removeEventListener('storage', handleStorageChange)
        window.removeEventListener('arknet-country-changed', handleCountryChange as EventListener)
      }
    }
  }, [])
  const [filterOptions, setFilterOptions] = useState({
    countries: [] as Array<{id: string, name: string}>,
    depots: [] as Array<{id: string, name: string}>,
    routes: [] as Array<{id: string, name: string}>,
    statuses: [
      { value: 'available', label: 'Available' },
      { value: 'maintenance', label: 'Maintenance' },
      { value: 'retired', label: 'Retired' }
    ]
  })



  // SAFE FILTERING - only runs when we have vehicles AND filters actually change
  useEffect(() => {
    if (vehicles.length > 0) {
      console.log('🔄 SAFE FILTERING - vehicles:', vehicles.length, 'filters:', JSON.stringify(filters))
      
      let filtered = vehicles

      // Text search
      if (filters.search && filters.search.trim() !== '') {
        const searchLower = filters.search.toLowerCase()
        filtered = filtered.filter(vehicle => 
          vehicle.reg_code?.toLowerCase().includes(searchLower) ||
          vehicle.notes?.toLowerCase().includes(searchLower)
        )
        console.log('� After search filter:', filtered.length)
      }

      // Filter by country - but be very careful here
      if (filters.country && filters.country.trim() !== '') {
        console.log('🌍 Filtering by country:', filters.country)
        console.log('🌍 First vehicle country_id:', vehicles[0]?.country_id)
        filtered = filtered.filter(vehicle => vehicle.country_id === filters.country)
        console.log('🌍 After country filter:', filtered.length)
      }

      // Filter by depot
      if (filters.depot && filters.depot.trim() !== '') {
        console.log('🏢 Filtering by depot:', filters.depot)
        filtered = filtered.filter(vehicle => vehicle.home_depot_id === filters.depot)
        console.log('🏢 After depot filter:', filtered.length)
      }

      // Filter by status - this should work!
      if (filters.status && filters.status.trim() !== '') {
        console.log('📊 Filtering by status:', filters.status)
        console.log('📊 Available statuses:', Array.from(new Set(vehicles.map(v => v.status))))
        filtered = filtered.filter(vehicle => vehicle.status === filters.status)
        console.log('📊 After status filter:', filtered.length)
      }

      console.log('✅ SAFE FILTER RESULT:', filtered.length, 'vehicles')
      setFilteredVehicles(filtered)
      setCurrentPage(1)
    }
  }, [vehicles, filters])

  const loadVehicles = async () => {
    setIsLoading(true)
    setError(null)
    try {
      // Use real API data
      const data = await dataProvider.getVehicles()
      
      // Transform API data to include lookup fields
      const vehiclesWithLookups = await Promise.all(
        data.map(async (vehicle: any) => ({
          ...vehicle,
          country_name: await getCountryName(vehicle.country_id),
          depot_name: vehicle.home_depot_id ? await getDepotName(vehicle.home_depot_id) : null,
          route_name: vehicle.preferred_route_id ? await getRouteName(vehicle.preferred_route_id) : null
        }))
      )
      setVehicles(vehiclesWithLookups)
      console.log('🚗 SET VEHICLES:', vehiclesWithLookups.length)
      
      // IMMEDIATE: Set filtered vehicles to show ALL vehicles initially
      setFilteredVehicles(vehiclesWithLookups)
      console.log('🔥 IMMEDIATE SET FILTERED VEHICLES:', vehiclesWithLookups.length)
      
    } catch (err) {
      setError('Failed to load vehicles')
      console.error('Error loading vehicles:', err)
      // Fallback to empty array on error
      setVehicles([])
      setFilteredVehicles([])
    } finally {
      setIsLoading(false)
    }
  }

  // Helper functions for lookups using real API data
  const getCountryName = async (countryId: string): Promise<string> => {
    try {
      const countries = await dataProvider.getCountries()
      const country = countries.find((c: any) => c.country_id === countryId)
      return country?.name || 'Unknown Country'
    } catch {
      return 'Unknown Country'
    }
  }

  const getDepotName = async (depotId: string): Promise<string> => {
    try {
      const depots = await dataProvider.getDepots()
      const depot = depots.find((d: any) => d.depot_id === depotId)
      return depot?.name || 'Unknown Depot'
    } catch {
      return 'Unknown Depot'
    }
  }

  const getRouteName = async (routeId: string): Promise<string> => {
    // Routes are not available in current API, return placeholder
    return 'No Route Assigned'
  }

  const applyFilters = () => {
    console.log('🔍 VEHICLES:', vehicles.length, 'FILTERS:', JSON.stringify(filters))
    let filtered = vehicles

    // Text search
    if (filters.search) {
      const searchLower = filters.search.toLowerCase()
      filtered = filtered.filter(vehicle => 
        vehicle.reg_code.toLowerCase().includes(searchLower) ||
        vehicle.notes?.toLowerCase().includes(searchLower) ||
        vehicle.depot_name?.toLowerCase().includes(searchLower) ||
        vehicle.country_name?.toLowerCase().includes(searchLower)
      )
      console.log('📝 After search:', filtered.length)
    }

    // Filter by country - only filter if country is set AND not empty
    if (filters.country && filters.country.trim() !== '') {
      console.log('🌍 Filtering by country:', filters.country)
      filtered = filtered.filter(vehicle => vehicle.country_id === filters.country)
      console.log('🌍 After country filter:', filtered.length)
    } else {
      console.log('🌍 No country filter - showing all vehicles')
    }

    // Filter by depot - only filter if depot is set
    if (filters.depot) {
      filtered = filtered.filter(vehicle => vehicle.home_depot_id === filters.depot)
      console.log('🏢 After depot filter:', filtered.length)
    }

    // Filter by route - only filter if route is set
    if (filters.route) {
      filtered = filtered.filter(vehicle => vehicle.preferred_route_id === filters.route)
      console.log('🛣️ After route filter:', filtered.length)
    }

    // Filter by status - only filter if status is set
    if (filters.status) {
      filtered = filtered.filter(vehicle => vehicle.status === filters.status)
      console.log('📊 After status filter:', filtered.length)
    }

    console.log('✅ FINAL RESULT:', filtered.length, 'vehicles')
    setFilteredVehicles(filtered)
    setCurrentPage(1)
  }

  const clearFilters = async () => {
    // Get the current global country to preserve it
    let globalCountry = ''
    if (typeof window !== 'undefined') {
      const savedCountry = localStorage.getItem('arknet-selected-country')
      if (savedCountry) {
        try {
          const country = JSON.parse(savedCountry)
          globalCountry = country.country_id
        } catch (error) {
          console.error('Failed to parse saved country:', error)
        }
      } else {
        // If no saved country, use the first available country
        try {
          const countries = await dataProvider.getCountries()
          if (countries.length > 0) {
            globalCountry = countries[0].country_id
          }
        } catch (error) {
          console.error('Failed to load default country:', error)
        }
      }
    }
    
    setFilters({
      ...INITIAL_FILTERS,
      country: globalCountry
    })
  }

  const handleFilterChange = (key: keyof VehicleFilters, value: string) => {
    setFilters(prev => ({ ...prev, [key]: value }))
  }

  const handleViewVehicle = (vehicle: Vehicle) => {
    console.log('View vehicle:', vehicle)
  }

  const handleEditVehicle = (vehicle: Vehicle) => {
    console.log('Edit vehicle:', vehicle)
  }

  const handleDeleteVehicle = async (vehicle: Vehicle) => {
    if (confirm(`Are you sure you want to delete vehicle ${vehicle.reg_code}?`)) {
      try {
        await loadVehicles()
      } catch (err) {
        alert('Failed to delete vehicle')
        console.error('Error deleting vehicle:', err)
      }
    }
  }

  // Load filter options from API
  const loadFilterOptions = async () => {
    console.log('📋 Loading filter options...')
    try {
      console.log('🌍 Calling getCountries...')
      const countriesData = await dataProvider.getCountries()
      console.log('🌍 Countries data received:', countriesData)
      
      console.log('🏢 Calling getDepots...')
      const depotsData = await dataProvider.getDepots()
      console.log('� Depots data received:', depotsData)
      
      console.log('🛣️ Calling getRoutes...')
      const routesData = await dataProvider.getRoutes()
      console.log('🛣️ Routes data received:', routesData)

      setFilterOptions(prev => ({
        ...prev,
        countries: countriesData.map((c: any) => ({ 
          id: c.country_id || c.id, 
          name: c.name || c.country_name || 'Unknown Country'
        })),
        depots: depotsData.map((d: any) => ({ 
          id: d.depot_id || d.id, 
          name: d.name || d.depot_name || 'Unknown Depot'
        })),
        routes: routesData.map((r: any) => ({ 
          id: r.route_id || r.id, 
          name: r.name || r.route_name || 'Unknown Route'
        }))
      }))
      
      console.log('✅ Filter options loaded successfully')
    } catch (error) {
      console.error('❌ Error loading filter options:', error)
      // Filter options will remain empty arrays
    }
  }

  // Pagination
  const totalPages = Math.ceil(filteredVehicles.length / VEHICLES_PER_PAGE)
  const paginatedVehicles = useMemo(() => {
    const startIndex = (currentPage - 1) * VEHICLES_PER_PAGE
    return filteredVehicles.slice(startIndex, startIndex + VEHICLES_PER_PAGE)
  }, [filteredVehicles, currentPage])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'text-green-600 bg-green-100 dark:text-green-400 dark:bg-green-900/20'
      case 'maintenance': return 'text-yellow-600 bg-yellow-100 dark:text-yellow-400 dark:bg-yellow-900/20'
      case 'out_of_service': return 'text-red-600 bg-red-100 dark:text-red-400 dark:bg-red-900/20'
      default: return 'text-gray-600 bg-gray-100 dark:text-gray-400 dark:bg-gray-900/20'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active': return CheckCircle
      case 'maintenance': return AlertTriangle
      case 'out_of_service': return XCircle
      default: return Car
    }
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <RefreshCw className="mx-auto h-8 w-8 animate-spin text-arknet-yellow" />
          <p className="mt-2 text-gray-600 dark:text-gray-400">Loading vehicles...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="vehicles-page p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Fleet Vehicles
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {isLoading ? (
              "Loading vehicles..."
            ) : (
              `Manage your fleet of ${filteredVehicles.length} vehicles`
            )}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          {/* View Mode Toggle */}
          <div className="flex rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <button
              onClick={() => setViewMode('card')}
              className={`p-2 rounded-l-lg transition-colors ${
                viewMode === 'card' 
                  ? 'bg-arknet-yellow text-white' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="Card View"
            >
              <Grid3x3 size={20} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-r-lg transition-colors ${
                viewMode === 'list' 
                  ? 'bg-arknet-yellow text-white' 
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
              }`}
              title="List View"
            >
              <List size={20} />
            </button>
          </div>

          {/* Add Vehicle Button */}
          <button className="flex items-center gap-2 px-4 py-2 bg-arknet-blue text-white rounded-lg hover:bg-arknet-blue/90 transition-colors">
            <Plus size={20} />
            Add Vehicle
          </button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        {/* Search */}
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" size={20} />
          <input
            type="text"
            placeholder="Search vehicles by registration, model, depot, or driver..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-arknet-yellow focus:border-transparent"
          />
        </div>

        {/* Filter Toggle */}
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition-colors ${
            showFilters 
              ? 'border-arknet-yellow bg-arknet-yellow/10 text-arknet-yellow' 
              : 'border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700'
          }`}
        >
          <Filter size={20} />
          Filters
          <ChevronDown className={`transform transition-transform ${showFilters ? 'rotate-180' : ''}`} size={16} />
        </button>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="filters-panel bg-gray-50 dark:bg-gray-800/50 rounded-lg p-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
            {/* Country Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Country
              </label>
              <select
                value={filters.country}
                onChange={(e) => handleFilterChange('country', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-arknet-yellow focus:border-transparent"
                aria-label="Filter by country"
              >
                <option value="">All Countries</option>
                {filterOptions.countries.map(country => (
                  <option key={country.id} value={country.id}>{country.name}</option>
                ))}
              </select>
            </div>

            {/* Depot Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Depot
              </label>
              <select
                value={filters.depot}
                onChange={(e) => handleFilterChange('depot', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-arknet-yellow focus:border-transparent"
                aria-label="Filter by depot"
              >
                <option value="">All Depots</option>
                {filterOptions.depots.map(depot => (
                  <option key={depot.id} value={depot.id}>{depot.name}</option>
                ))}
              </select>
            </div>

            {/* Route Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Route
              </label>
              <select
                value={filters.route}
                onChange={(e) => handleFilterChange('route', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-arknet-yellow focus:border-transparent"
                aria-label="Filter by route"
              >
                <option value="">All Routes</option>
                {filterOptions.routes.map(route => (
                  <option key={route.id} value={route.id}>{route.name}</option>
                ))}
              </select>
            </div>

            {/* Status Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-arknet-yellow focus:border-transparent"
                aria-label="Filter by status"
              >
                <option value="">All Statuses</option>
                {filterOptions.statuses.map(status => (
                  <option key={status.value} value={status.value}>{status.label}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Clear Filters */}
          <button
            onClick={clearFilters}
            className="flex items-center gap-2 px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
          >
            <X size={16} />
            Clear all filters
          </button>
        </div>
      )}

      {/* Results Summary */}
      <div className="flex justify-between items-center text-sm text-gray-600 dark:text-gray-400">
        <span>
          {isLoading ? (
            "Loading vehicles..."
          ) : (
            `Showing ${paginatedVehicles.length} of ${filteredVehicles.length} vehicles`
          )}
        </span>
        {totalPages > 1 && !isLoading && (
          <span>
            Page {currentPage} of {totalPages}
          </span>
        )}
      </div>

      {/* Vehicles Grid/List */}
      {viewMode === 'card' ? (
        <VehicleCardGrid 
          vehicles={paginatedVehicles}
          onView={handleViewVehicle}
          onEdit={handleEditVehicle}
          onDelete={handleDeleteVehicle}
          getStatusColor={getStatusColor}
          getStatusIcon={getStatusIcon}
        />
      ) : (
        <VehicleListView 
          vehicles={paginatedVehicles}
          onView={handleViewVehicle}
          onEdit={handleEditVehicle}
          onDelete={handleDeleteVehicle}
          getStatusColor={getStatusColor}
          getStatusIcon={getStatusIcon}
        />
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Pagination 
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={setCurrentPage}
        />
      )}

      {/* Error Display */}
      {error && (
        <div className="fixed bottom-4 right-4 bg-red-100 dark:bg-red-900/20 border border-red-200 dark:border-red-800 text-red-700 dark:text-red-400 px-4 py-2 rounded-lg">
          {error}
        </div>
      )}
    </div>
  )
}

// Vehicle Card Grid Component
function VehicleCardGrid({ 
  vehicles, 
  onView, 
  onEdit, 
  onDelete, 
  getStatusColor, 
  getStatusIcon 
}: {
  vehicles: Vehicle[]
  onView: (vehicle: Vehicle) => void
  onEdit: (vehicle: Vehicle) => void
  onDelete: (vehicle: Vehicle) => void
  getStatusColor: (status: string) => string
  getStatusIcon: (status: string) => any
}) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {vehicles.map((vehicle) => {
        const StatusIcon = getStatusIcon(vehicle.status)
        return (
          <div
            key={vehicle.vehicle_id}
            className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-all duration-200 transform hover:-translate-y-1"
          >
            {/* Card Header */}
            <div className="p-4 pb-2">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <div className="h-8 w-8 bg-arknet-blue rounded-full flex items-center justify-center">
                    <Car className="h-4 w-4 text-white" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white text-sm">
                      {vehicle.reg_code}
                    </h3>
                  </div>
                </div>
                <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(vehicle.status)}`}>
                  <StatusIcon className="h-3 w-3 mr-1" />
                  {vehicle.status.replace('_', ' ').toUpperCase()}
                </span>
              </div>
            </div>

            {/* Card Body */}
            <div className="px-4 pb-4">
              <div className="space-y-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Country:</span>
                  <span className="text-gray-900 dark:text-white font-medium">{vehicle.country_name || 'Unknown'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Notes:</span>
                  <span className="text-gray-900 dark:text-white">{vehicle.notes || 'None'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Depot:</span>
                  <span className="text-gray-900 dark:text-white">{vehicle.depot_name || 'Unassigned'}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500 dark:text-gray-400">Created:</span>
                  <span className="text-gray-900 dark:text-white">{new Date(vehicle.created_at).toLocaleDateString()}</span>
                </div>
                {vehicle.route_name && (
                  <div className="flex justify-between">
                    <span className="text-gray-500 dark:text-gray-400">Route:</span>
                    <span className="text-gray-900 dark:text-white">{vehicle.route_name}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Card Actions */}
            <div className="border-t border-gray-200 dark:border-gray-700 px-4 py-3">
              <div className="flex space-x-2">
                <button
                  onClick={() => onView(vehicle)}
                  className="flex-1 flex items-center justify-center px-2 py-1 text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                  title="View Vehicle Details"
                >
                  <Eye className="h-3 w-3 mr-1" />
                  View
                </button>
                <button
                  onClick={() => onEdit(vehicle)}
                  className="flex-1 flex items-center justify-center px-2 py-1 text-xs bg-arknet-yellow text-white rounded hover:bg-arknet-yellow/90 transition-colors"
                  title="Edit Vehicle"
                >
                  <Edit className="h-3 w-3 mr-1" />
                  Edit
                </button>
                <button
                  onClick={() => onDelete(vehicle)}
                  className="flex-1 flex items-center justify-center px-2 py-1 text-xs bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded hover:bg-red-200 dark:hover:bg-red-900/40 transition-colors"
                  title="Delete Vehicle"
                >
                  <Trash2 className="h-3 w-3 mr-1" />
                  Delete
                </button>
              </div>
            </div>
          </div>
        )
      })}
    </div>
  )
}

// Vehicle List View Component
function VehicleListView({ 
  vehicles, 
  onView, 
  onEdit, 
  onDelete, 
  getStatusColor, 
  getStatusIcon 
}: {
  vehicles: Vehicle[]
  onView: (vehicle: Vehicle) => void
  onEdit: (vehicle: Vehicle) => void
  onDelete: (vehicle: Vehicle) => void
  getStatusColor: (status: string) => string
  getStatusIcon: (status: string) => any
}) {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900/50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Vehicle
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Model & Capacity
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Assignment
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {vehicles.map((vehicle) => {
              const StatusIcon = getStatusIcon(vehicle.status)
              return (
                <tr key={vehicle.vehicle_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="h-8 w-8 bg-arknet-blue rounded-full flex items-center justify-center">
                        <Car className="h-4 w-4 text-white" />
                      </div>
                      <div className="ml-3">
                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                          {vehicle.reg_code}
                        </div>
                        <div className="text-sm text-gray-500 dark:text-gray-400">
                          {vehicle.country_name || 'Unknown Country'}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">{vehicle.notes || 'No notes'}</div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Created: {new Date(vehicle.created_at).toLocaleDateString()}</div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm text-gray-900 dark:text-white">
                      {vehicle.depot_name || 'Unassigned'}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">
                      {vehicle.route_name || 'No route'}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(vehicle.status)}`}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {vehicle.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <div className="flex justify-end space-x-2">
                      <button
                        onClick={() => onView(vehicle)}
                        className="text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white"
                        title="View Vehicle Details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onEdit(vehicle)}
                        className="text-arknet-yellow hover:text-arknet-yellow/80"
                        title="Edit Vehicle"
                      >
                        <Edit className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => onDelete(vehicle)}
                        className="text-red-600 dark:text-red-400 hover:text-red-800 dark:hover:text-red-300"
                        title="Delete Vehicle"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// Pagination Component
function Pagination({ 
  currentPage, 
  totalPages, 
  onPageChange 
}: {
  currentPage: number
  totalPages: number
  onPageChange: (page: number) => void
}) {
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const showPages = 5

    if (totalPages <= showPages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      pages.push(1)
      
      if (currentPage > 3) {
        pages.push('...')
      }
      
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)
      
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      if (currentPage < totalPages - 2) {
        pages.push('...')
      }
      
      pages.push(totalPages)
    }

    return pages
  }

  return (
    <div className="flex items-center justify-between">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={currentPage === 1}
        className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Previous
      </button>
      
      <div className="flex space-x-1">
        {getPageNumbers().map((page, index) => (
          <button
            key={index}
            onClick={() => typeof page === 'number' && onPageChange(page)}
            disabled={page === '...' || page === currentPage}
            className={`px-3 py-2 text-sm rounded-lg ${
              page === currentPage
                ? 'bg-arknet-yellow text-white'
                : page === '...'
                ? 'text-gray-400 dark:text-gray-600 cursor-default'
                : 'bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700'
            }`}
          >
            {page}
          </button>
        ))}
      </div>
      
      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={currentPage === totalPages}
        className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        Next
      </button>
    </div>
  )
}
