/**
 * ROUTES PAGE - Route Management (App Router)
 */

import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Routes',
  description: 'Manage your transit routes'
}

export default function RoutesPage() {
  return (
    <main className="main-content">
      <div className="page-header">
        <h1 className="text-3xl font-bold text-gray-900">Route Management</h1>
        <p className="text-gray-600">Manage your transit routes and schedules</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div className="flex space-x-4">
              <input
                type="text"
                placeholder="Search routes..."
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                aria-label="Route status"
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Routes</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="MAINTENANCE">Under Maintenance</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <Link
                href="/routes/new"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Add Route
              </Link>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Import Routes
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-1.447-.894L15 4m0 13V4m-6 3l6-3" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Routes Coming Soon</h3>
            <p className="text-gray-500 mb-4">Route management functionality will be available soon</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mt-8">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Available Endpoints</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Stops</li>
                  <li>• Services</li>
                  <li>• Trips</li>
                  <li>• Blocks</li>
                </ul>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Working Pages</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>
                    <Link href="/vehicles" className="hover:underline">• Vehicles</Link>
                  </li>
                  <li>
                    <Link href="/drivers" className="hover:underline">• Drivers</Link>
                  </li>
                </ul>
              </div>
              
              <div className="bg-yellow-50 p-4 rounded-lg">
                <h4 className="font-medium text-yellow-900 mb-2">Status</h4>
                <p className="text-sm text-yellow-700">
                  Real API connected<br/>
                  Mock API eliminated<br/>
                  Database integrated
                </p>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-medium text-purple-900 mb-2">API Docs</h4>
                <div className="text-sm text-purple-700 space-y-1">
                  <a 
                    href="http://localhost:8000/docs" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block hover:underline"
                  >
                    • Swagger UI
                  </a>
                  <a 
                    href="http://localhost:8000/redoc" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="block hover:underline"
                  >
                    • ReDoc
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
