/**
 * DASHBOARD CLIENT COMPONENT - App Router Client Component
 * This handles the interactive dashboard functionality
 */

'use client'

import { useEffect, useState } from 'react'
import { getAppInstance } from '@/app'
import { dataProvider } from '@/infrastructure/data-provider'
import FleetCharts from '@/components/FleetCharts'
import { 
  Truck, 
  Users, 
  Map, 
  RefreshCw, 
  AlertCircle,
  X,
  Plus,
  Activity,
  TrendingUp,
  Clock,
  CheckCircle,
  AlertTriangle,
  XCircle
} from 'lucide-react'

interface DashboardStats {
  vehicleStats: {
    total: number
    active: number
    maintenance: number
    outOfService: number
  }
  driverStats: {
    total: number
    available: number
    onDuty: number
    onLeave: number
  }
  routeStats: {
    total: number
    active: number
  }
}

interface DashboardClientProps {
  data: DashboardStats
}

export default function DashboardClient({ data }: DashboardClientProps) {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Initialize the Fleet Management Application
    const app = getAppInstance()
    app.initialize().catch((err) => {
      setError('Failed to initialize application')
      console.error('App initialization error:', err)
    })
  }, [])

  const handleRefreshData = async () => {
    setIsLoading(true)
    try {
      // Refresh dashboard data from API
      const stats = await dataProvider.getDashboardStats()
      // TODO: Update dashboard state with real data
      console.log('Dashboard stats:', stats)
    } catch (err) {
      setError('Failed to refresh data')
    } finally {
      setIsLoading(false)
    }
  }

  const quickActions = [
    { label: 'Manage Vehicles', href: '/vehicles', icon: Truck },
    { label: 'Add Vehicle', href: '/vehicles/new', icon: Plus },
    { label: 'Add Driver', href: '/drivers/new', icon: Users },
    { label: 'Create Route', href: '/routes/new', icon: Map },
    { label: 'Import Data', href: '/import', icon: TrendingUp }
  ]

  // TODO: Replace with actual Material-UI components once installed
  return (
    <div className="dashboard-container">
      <header className="dashboard-header">
        <h1>Fleet Management Dashboard</h1>
        <button 
          onClick={handleRefreshData}
          disabled={isLoading}
          className="refresh-button"
        >
          <RefreshCw size={16} className={isLoading ? 'animate-spin' : ''} />
          {isLoading ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </header>

      {error && (
        <div className="error-banner">
          <div className="flex items-center">
            <AlertCircle size={20} className="mr-2" />
            <p>Error: {error}</p>
          </div>
          <button onClick={() => setError(null)} title="Dismiss error">
            <X size={16} />
          </button>
        </div>
      )}

      <div className="stats-grid">
        {/* Vehicles Stats */}
        <div className="stat-card">
          <h2><Truck size={20} />Vehicles</h2>
          <div className="stat-number">{data.vehicleStats.total}</div>
          <div className="stat-breakdown">
            <div><CheckCircle size={16} className="text-green-500" />Active: {data.vehicleStats.active}</div>
            <div><AlertTriangle size={16} className="text-yellow-500" />Maintenance: {data.vehicleStats.maintenance}</div>
            <div><XCircle size={16} className="text-red-500" />Out of Service: {data.vehicleStats.outOfService}</div>
          </div>
          {data.vehicleStats.total === 0 && (
            <div className="empty-state-hint">
              <p>No vehicles in your fleet yet.</p>
              <a href="/vehicles/new" className="action-link">Add your first vehicle</a>
            </div>
          )}
        </div>

        {/* Drivers Stats */}
        <div className="stat-card">
          <h2><Users size={20} />Drivers</h2>
          <div className="stat-number">{data.driverStats.total}</div>
          <div className="stat-breakdown">
            <div><CheckCircle size={16} className="text-green-500" />Available: {data.driverStats.available}</div>
            <div><Clock size={16} className="text-blue-500" />On Duty: {data.driverStats.onDuty}</div>
            <div><AlertCircle size={16} className="text-gray-500" />On Leave: {data.driverStats.onLeave}</div>
          </div>
          {data.driverStats.total === 0 && (
            <div className="empty-state-hint">
              <p>No drivers registered yet.</p>
              <a href="/drivers/new" className="action-link">Add your first driver</a>
            </div>
          )}
        </div>

        {/* Routes Stats */}
        <div className="stat-card">
          <h2><Map size={20} />Routes</h2>
          <div className="stat-number">{data.routeStats.total}</div>
          <div className="stat-breakdown">
            <div><Activity size={16} className="text-green-500" />Active: {data.routeStats.active}</div>
          </div>
          {data.routeStats.total === 0 && (
            <div className="empty-state-hint">
              <p>No routes defined yet.</p>
              <a href="/routes/new" className="action-link">Create your first route</a>
            </div>
          )}
        </div>
      </div>

      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          {quickActions.map((action, index) => {
            const IconComponent = action.icon
            return (
              <a
                key={index}
                href={action.href}
                className="action-button"
              >
                <IconComponent size={18} />
                {action.label}
              </a>
            )
          })}
        </div>
      </div>

      <FleetCharts vehicleStats={data.vehicleStats} driverStats={data.driverStats} />

      <div className="recent-activity">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          {data.vehicleStats.total > 0 || data.driverStats.total > 0 ? (
            <>
              <div className="activity-item">2 minutes ago: Vehicle BBX-1234 assigned to Route 15</div>
              <div className="activity-item">15 minutes ago: Driver John Smith started shift</div>
              <div className="activity-item">1 hour ago: Vehicle maintenance completed for ABC-5678</div>
              <div className="activity-item">2 hours ago: New route "Downtown Express" created</div>
            </>
          ) : (
            <div className="empty-activity">
              <p>🚀 Welcome to Fleet Management!</p>
              <p>Once you start adding vehicles, drivers, and routes, you'll see recent activity here.</p>
              <div className="getting-started">
                <h3>Getting Started:</h3>
                <ol>
                  <li><a href="/vehicles/new">Add your first vehicle</a></li>
                  <li><a href="/drivers/new">Register your drivers</a></li>
                  <li><a href="/routes/new">Define your routes</a></li>
                  <li>Start scheduling and tracking!</li>
                </ol>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
