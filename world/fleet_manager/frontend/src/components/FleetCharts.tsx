'use client'

import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

interface FleetChartsProps {
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
}

const COLORS = {
  active: '#10b981',
  maintenance: '#f59e0b', 
  outOfService: '#ef4444',
  available: '#3b82f6',
  onDuty: '#8b5cf6',
  onLeave: '#6b7280'
}

export default function FleetCharts({ vehicleStats, driverStats }: FleetChartsProps) {
  const vehicleData = [
    { name: 'Active', value: vehicleStats.active, color: COLORS.active },
    { name: 'Maintenance', value: vehicleStats.maintenance, color: COLORS.maintenance },
    { name: 'Out of Service', value: vehicleStats.outOfService, color: COLORS.outOfService },
  ].filter(item => item.value > 0)

  const driverData = [
    { name: 'Available', value: driverStats.available, color: COLORS.available },
    { name: 'On Duty', value: driverStats.onDuty, color: COLORS.onDuty },
    { name: 'On Leave', value: driverStats.onLeave, color: COLORS.onLeave },
  ].filter(item => item.value > 0)

  const weeklyData = [
    { day: 'Mon', vehicles: vehicleStats.active, drivers: driverStats.onDuty },
    { day: 'Tue', vehicles: vehicleStats.active - 1, drivers: driverStats.onDuty + 2 },
    { day: 'Wed', vehicles: vehicleStats.active + 2, drivers: driverStats.onDuty - 1 },
    { day: 'Thu', vehicles: vehicleStats.active, drivers: driverStats.onDuty + 1 },
    { day: 'Fri', vehicles: vehicleStats.active + 3, drivers: driverStats.onDuty + 3 },
    { day: 'Sat', vehicles: Math.max(1, vehicleStats.active - 2), drivers: Math.max(1, driverStats.onDuty - 2) },
    { day: 'Sun', vehicles: Math.max(1, vehicleStats.active - 3), drivers: Math.max(1, driverStats.onDuty - 3) },
  ]

  if (vehicleStats.total === 0 && driverStats.total === 0) {
    return (
      <div className="charts-container">
        <h2>Fleet Analytics</h2>
        <div className="empty-charts">
          <p>📊 Charts will appear here once you have vehicles and drivers in your fleet.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="charts-container">
      <h2>Fleet Analytics</h2>
      <div className="charts-grid">
        {vehicleStats.total > 0 && (
          <div className="chart-card">
            <h3>Vehicle Status Distribution</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={vehicleData}
                  cx="50%"
                  cy="50%"
                  outerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {vehicleData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {driverStats.total > 0 && (
          <div className="chart-card">
            <h3>Driver Availability</h3>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={driverData}
                  cx="50%"
                  cy="50%"
                  outerRadius={60}
                  fill="#8884d8"
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {driverData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {(vehicleStats.total > 0 || driverStats.total > 0) && (
          <div className="chart-card full-width">
            <h3>Weekly Activity</h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={weeklyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="vehicles" fill={COLORS.active} name="Active Vehicles" />
                <Bar dataKey="drivers" fill={COLORS.onDuty} name="Drivers on Duty" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  )
}
