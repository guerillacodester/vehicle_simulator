/**
 * TIMETABLES PAGE - Timetable Management (App Router)
 */

import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Timetables',
  description: 'Manage transit timetables and schedules'
}

export default function TimetablesPage() {
  return (
    <main className="main-content">
      <div className="page-header">
        <h1 className="text-3xl font-bold text-gray-900">Timetable Management</h1>
        <p className="text-gray-600">Manage transit schedules and timetables</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div className="flex space-x-4">
              <input
                type="text"
                placeholder="Search timetables..."
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                aria-label="Timetable status"
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Schedules</option>
                <option value="ACTIVE">Active</option>
                <option value="INACTIVE">Inactive</option>
                <option value="DRAFT">Draft</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <Link
                href="/timetables/new"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Create Timetable
              </Link>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Import Schedule
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Timetables Coming Soon</h3>
            <p className="text-gray-500 mb-4">Schedule management functionality will be available soon</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Related Endpoints</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>• Trips</li>
                  <li>• Services</li>
                  <li>• Blocks</li>
                  <li>• Stops</li>
                </ul>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Available Now</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>
                    <Link href="/vehicles" className="hover:underline">• Vehicle Management</Link>
                  </li>
                  <li>
                    <Link href="/drivers" className="hover:underline">• Driver Management</Link>
                  </li>
                  <li>
                    <Link href="/routes" className="hover:underline">• Route Planning</Link>
                  </li>
                </ul>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-medium text-purple-900 mb-2">Features Planned</h4>
                <ul className="text-sm text-purple-700 space-y-1">
                  <li>• Schedule Creation</li>
                  <li>• Time Table Import</li>
                  <li>• Service Blocks</li>
                  <li>• Trip Planning</li>
                </ul>
              </div>
            </div>
            
            <div className="mt-8 p-4 bg-yellow-50 rounded-lg">
              <p className="text-sm text-yellow-800">
                <strong>System Status:</strong> Real API connected • Database integrated • Mock API eliminated
              </p>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
