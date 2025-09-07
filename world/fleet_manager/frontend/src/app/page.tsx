/**
 * DASHBOARD PAGE - App Router Home Page
 * This is the default page that loads when users access the fleet management system
 */

import { Metadata } from 'next'
import DashboardClient from './dashboard-client'
import { dataProvider } from '@/infrastructure/data-provider'

export const metadata: Metadata = {
  title: 'Dashboard',
  description: 'Overview of fleet operations, vehicles, drivers, and routes'
}

// Server Component - handles data fetching and static content
export default async function DashboardPage() {
  let dashboardData;
  
  try {
    // Try to fetch real data from the API
    dashboardData = await dataProvider.getDashboardStats();
  } catch (error) {
    console.warn('Failed to fetch dashboard data from API, using fallback data:', error);
    // Fallback data if API is unavailable
    dashboardData = {
      vehicleStats: {
        total: 0,
        active: 0,
        maintenance: 0,
        outOfService: 0
      },
      driverStats: {
        total: 0,
        available: 0,
        onDuty: 0,
        onLeave: 0
      },
      routeStats: {
        total: 0,
        active: 0
      }
    };
  }

  return (
    <main className="main-content">
      <DashboardClient data={dashboardData} />
    </main>
  )
}
