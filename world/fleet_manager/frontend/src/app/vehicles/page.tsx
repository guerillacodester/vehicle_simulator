/**
 * VEHICLES PAGE - App Router Vehicle Management Page
 */

import { Metadata } from 'next'
import VehiclesClient from './vehicles-client'

export const metadata: Metadata = {
  title: 'Fleet Vehicles | Fleet Management',
  description: 'Manage your fleet vehicles - add, edit, and track vehicle status'
}

// Server Component - handles initial setup
export default async function VehiclesPage() {
  return <VehiclesClient />
}
