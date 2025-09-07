/**
 * DASHBOARD PAGE - App Router Home Page
 * This is the default page that loads when users access the fleet management system
 */

import { Metadata } from 'next'
import DashboardClient from './dashboard-client'

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Overview of fleet operations, vehicles, drivers, and routes'
}

// Server Component - handles data fetching and static content
export default async function DashboardPage() {
  // TODO: Fetch real data from API in production
  const dashboardData = {
    vehicleStats: {
      total: 45,
      active: 38,
      maintenance: 5,
      outOfService: 2
    },
    driverStats: {
      total: 52,
      available: 15,
      onDuty: 35,
      onLeave: 2
    },
    routeStats: {
      total: 12,
      active: 10
    }
  }

  return (
    <main className="main-content">
      <DashboardClient data={dashboardData} />
    </main>
  )
}
