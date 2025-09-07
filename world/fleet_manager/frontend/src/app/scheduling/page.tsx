/**
 * SCHEDULING PAGE - Vehicle and Driver Scheduling (App Router)
 */

import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Scheduling',
  description: 'Manage vehicle and driver scheduling'
}

export default function SchedulingPage() {
  return (
    <main className="main-content">
      <div className="page-header">
        <h1 className="text-3xl font-bold text-gray-900">Scheduling</h1>
        <p className="text-gray-600">Manage vehicle and driver assignments</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <div className="flex space-x-4">
              <input
                type="text"
                placeholder="Search schedules..."
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <select
                aria-label="Schedule type"
                className="border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">All Types</option>
                <option value="VEHICLE">Vehicle Schedule</option>
                <option value="DRIVER">Driver Schedule</option>
                <option value="ROUTE">Route Assignment</option>
              </select>
            </div>
            <div className="flex space-x-2">
              <Link
                href="/scheduling/new"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Create Schedule
              </Link>
              <button className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50">
                Auto Schedule
              </button>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">
              <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Scheduling System Coming Soon</h3>
            <p className="text-gray-500 mb-4">Advanced scheduling and assignment tools will be available soon</p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
              <div className="bg-blue-50 p-4 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Current Resources</h4>
                <ul className="text-sm text-blue-700 space-y-1">
                  <li>
                    <Link href="/vehicles" className="hover:underline">• 4 Vehicles Available</Link>
                  </li>
                  <li>
                    <Link href="/drivers" className="hover:underline">• 4 Drivers Active</Link>
                  </li>
                </ul>
              </div>
              
              <div className="bg-green-50 p-4 rounded-lg">
                <h4 className="font-medium text-green-900 mb-2">Scheduling Features</h4>
                <ul className="text-sm text-green-700 space-y-1">
                  <li>• Vehicle Assignment</li>
                  <li>• Driver Allocation</li>
                  <li>• Route Scheduling</li>
                  <li>• Shift Management</li>
                </ul>
              </div>
              
              <div className="bg-purple-50 p-4 rounded-lg">
                <h4 className="font-medium text-purple-900 mb-2">Integration</h4>
                <ul className="text-sm text-purple-700 space-y-1">
                  <li>• Real-time Updates</li>
                  <li>• Conflict Detection</li>
                  <li>• Optimization Engine</li>
                  <li>• Reporting Tools</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
