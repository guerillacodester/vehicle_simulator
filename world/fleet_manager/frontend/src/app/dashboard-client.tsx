/**
 * DASHBOARD CLIENT COMPONENT - App Router Client Component
 * This handles the interactive dashboard functionality
 */

'use client'

import { useEffect, useState } from 'react'
import { getAppInstance } from '@/app'

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
      // TODO: Refresh dashboard data from API
      await new Promise(resolve => setTimeout(resolve, 1000)) // Mock delay
    } catch (err) {
      setError('Failed to refresh data')
    } finally {
      setIsLoading(false)
    }
  }

  const quickActions = [
    { label: 'Manage Vehicles', href: '/vehicles' },
    { label: 'Add Vehicle', href: '/vehicles/new' },
    { label: 'Add Driver', href: '/drivers/new' },
    { label: 'Create Route', href: '/routes/new' },
    { label: 'Import Data', href: '/import' }
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
          {isLoading ? 'Refreshing...' : 'Refresh Data'}
        </button>
      </header>

      {error && (
        <div className="error-banner">
          <p>Error: {error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}

      <div className="stats-grid">
        {/* Vehicles Stats */}
        <div className="stat-card">
          <h2>Vehicles</h2>
          <div className="stat-number">{data.vehicleStats.total}</div>
          <div className="stat-breakdown">
            <div>Active: {data.vehicleStats.active}</div>
            <div>Maintenance: {data.vehicleStats.maintenance}</div>
            <div>Out of Service: {data.vehicleStats.outOfService}</div>
          </div>
        </div>

        {/* Drivers Stats */}
        <div className="stat-card">
          <h2>Drivers</h2>
          <div className="stat-number">{data.driverStats.total}</div>
          <div className="stat-breakdown">
            <div>Available: {data.driverStats.available}</div>
            <div>On Duty: {data.driverStats.onDuty}</div>
            <div>On Leave: {data.driverStats.onLeave}</div>
          </div>
        </div>

        {/* Routes Stats */}
        <div className="stat-card">
          <h2>Routes</h2>
          <div className="stat-number">{data.routeStats.total}</div>
          <div className="stat-breakdown">
            <div>Active: {data.routeStats.active}</div>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="actions-grid">
          {quickActions.map((action, index) => (
            <a
              key={index}
              href={action.href}
              className="action-button"
            >
              {action.label}
            </a>
          ))}
        </div>
      </div>

      <div className="recent-activity">
        <h2>Recent Activity</h2>
        <div className="activity-list">
          <div className="activity-item">2 minutes ago: Vehicle BBX-1234 assigned to Route 15</div>
          <div className="activity-item">15 minutes ago: Driver John Smith started shift</div>
          <div className="activity-item">1 hour ago: Vehicle maintenance completed for ABC-5678</div>
          <div className="activity-item">2 hours ago: New route "Downtown Express" created</div>
        </div>
      </div>
    </div>
  )
}
