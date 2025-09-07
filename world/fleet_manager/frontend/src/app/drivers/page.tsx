/**
 * DRIVERS PAGE - Driver Management (App Router)
 */

import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Drivers',
  description: 'Manage your fleet drivers'
}

export default async function DriversPage() {
  // TODO: Fetch drivers data from API in production
  const drivers: unknown[] = []

  return (
    <main className="main-content">
      <div className="page-header">
        <h1 className="text-3xl font-bold text-gray-900">Driver Management</h1>
        <p className="text-gray-600">Manage your fleet drivers</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div className="flex space-x-4">
              <input
                type="text"
                placeholder="Search drivers..."
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                aria-label="Driver status"
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Status</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="ON_LEAVE">On Leave</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <Link
                href="/drivers/new"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Add Driver
              </Link>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Import Drivers
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          {drivers.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-500 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">No drivers found</h3>
              <p className="text-gray-500 mb-4">Get started by adding your first driver</p>
              <Link
                href="/drivers/new"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add Driver
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full table-auto">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Employee ID</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Name</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">License Number</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-900">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {/* Driver rows will be rendered here */}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
