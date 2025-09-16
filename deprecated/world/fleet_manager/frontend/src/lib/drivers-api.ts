/**
 * Drivers API Functions - Server-side data fetching
 */

import { dataProvider } from '@/infrastructure/data-provider'

export interface DriverData {
  driver_id: string
  country_id: string
  name: string
  license_no: string
  home_depot_id: string | null
  employment_status: string
  created_at: string
  updated_at: string
}

export interface Driver {
  id: string
  employeeId: string
  firstName: string
  lastName: string
  licenseNumber: string
  status: string
  createdAt: Date
  updatedAt: Date
}

function mapDriverData(apiDriver: DriverData): Driver {
  const [firstName, ...lastNameParts] = apiDriver.name.split(' ')
  const lastName = lastNameParts.join(' ')

  return {
    id: apiDriver.driver_id,
    employeeId: apiDriver.driver_id.slice(0, 8),
    firstName: firstName || '',
    lastName: lastName || '',
    licenseNumber: apiDriver.license_no,
    status: apiDriver.employment_status,
    createdAt: new Date(apiDriver.created_at),
    updatedAt: new Date(apiDriver.updated_at)
  }
}

export async function getDrivers(): Promise<Driver[]> {
  try {
    const response = await dataProvider.get<DriverData[]>('/api/v1/drivers')
    return response.map(mapDriverData)
  } catch (error) {
    console.error('Failed to fetch drivers:', error)
    throw new Error('Failed to load drivers data')
  }
}
