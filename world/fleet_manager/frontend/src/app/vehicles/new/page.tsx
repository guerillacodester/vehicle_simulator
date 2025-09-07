/**
 * ADD VEHICLE PAGE - New Vehicle Form (App Router)
 */

import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Add Vehicle',
  description: 'Add a new vehicle to your fleet'
}

export default function AddVehiclePage() {
  return (
    <main className="main-content">
      <div className="page-header">
        <nav className="breadcrumbs mb-4">
          <Link href="/" className="text-blue-600 hover:text-blue-800">Home</Link>
          <span className="mx-2">/</span>
          <Link href="/vehicles" className="text-blue-600 hover:text-blue-800">Vehicles</Link>
          <span className="mx-2">/</span>
          <span className="text-gray-500">Add Vehicle</span>
        </nav>
        
        <h1 className="text-3xl font-bold text-gray-900">Add New Vehicle</h1>
        <p className="text-gray-600">Enter vehicle details to add to your fleet</p>
      </div>
      
      <div className="bg-white rounded-lg shadow-md p-6">
        <form className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label htmlFor="plateNumber" className="block text-sm font-medium text-gray-700">
                Plate Number *
              </label>
              <input
                type="text"
                id="plateNumber"
                name="plateNumber"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter plate number"
              />
            </div>
            
            <div>
              <label htmlFor="model" className="block text-sm font-medium text-gray-700">
                Vehicle Model *
              </label>
              <input
                type="text"
                id="model"
                name="model"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter vehicle model"
              />
            </div>
            
            <div>
              <label htmlFor="capacity" className="block text-sm font-medium text-gray-700">
                Passenger Capacity *
              </label>
              <input
                type="number"
                id="capacity"
                name="capacity"
                required
                min="1"
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter capacity"
              />
            </div>
            
            <div>
              <label htmlFor="regCode" className="block text-sm font-medium text-gray-700">
                Registration Code
              </label>
              <input
                type="text"
                id="regCode"
                name="regCode"
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter registration code"
              />
            </div>
            
            <div>
              <label htmlFor="status" className="block text-sm font-medium text-gray-700">
                Status *
              </label>
              <select
                id="status"
                name="status"
                required
                className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="ACTIVE">Active</option>
                <option value="MAINTENANCE">In Maintenance</option>
                <option value="OUT_OF_SERVICE">Out of Service</option>
              </select>
            </div>
          </div>
          
          <div className="flex justify-end space-x-4 pt-6 border-t">
            <Link
              href="/vehicles"
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Cancel
            </Link>
            <button
              type="button"
              className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Reset Form
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Save Vehicle
            </button>
          </div>
        </form>
      </div>
    </main>
  )
}
