'use client';

import { useState, useEffect } from 'react';

// Mock data for initial development
const mockVehicles = [
  {
    id: 1,
    registration: 'ZR001',
    type: 'bus',
    status: 'available',
    driver: { name: 'John Driver' },
    route: { code: '1', name: 'Route 1 - Main Line' }
  }
];

const mockSimulatorStatus = {
  connected: true,
  vehicles: 1,
  drivers: 1,
  operational: true
};

export default function ArkNetControlCenter() {
  const [vehicles, setVehicles] = useState(mockVehicles);
  const [simulatorStatus, setSimulatorStatus] = useState(mockSimulatorStatus);
  const [isLoading, setIsLoading] = useState(false);

  const handleStartSimulation = async () => {
    setIsLoading(true);
    // Future: Call API to start simulation
    setTimeout(() => {
      setIsLoading(false);
      // Mock status update
      setSimulatorStatus(prev => ({ ...prev, operational: !prev.operational }));
    }, 2000);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-blue-900 text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-3xl font-bold">🚌 ArkNet Transit Control Center</h1>
          <p className="text-blue-200 mt-2">Fleet Management & Simulation Dashboard</p>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Status Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className={`w-4 h-4 rounded-full mr-3 ${simulatorStatus.connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <div>
                <p className="text-sm text-gray-500">System Status</p>
                <p className="text-lg font-semibold">{simulatorStatus.connected ? 'Connected' : 'Disconnected'}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <span className="text-2xl mr-3">🚐</span>
              <div>
                <p className="text-sm text-gray-500">Active Vehicles</p>
                <p className="text-lg font-semibold">{simulatorStatus.vehicles}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <span className="text-2xl mr-3">👨‍✈️</span>
              <div>
                <p className="text-sm text-gray-500">On-Duty Drivers</p>
                <p className="text-lg font-semibold">{simulatorStatus.drivers}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <span className={`text-2xl mr-3 ${simulatorStatus.operational ? '🟢' : '🔴'}`}></span>
              <div>
                <p className="text-sm text-gray-500">Operations</p>
                <p className="text-lg font-semibold">{simulatorStatus.operational ? 'Running' : 'Stopped'}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-4">Simulation Controls</h2>
          <div className="flex gap-4">
            <button
              onClick={handleStartSimulation}
              disabled={isLoading}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                simulatorStatus.operational
                  ? 'bg-red-600 hover:bg-red-700 text-white'
                  : 'bg-green-600 hover:bg-green-700 text-white'
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {isLoading ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </span>
              ) : (
                simulatorStatus.operational ? 'Stop Simulation' : 'Start Simulation'
              )}
            </button>
            
            <button className="px-6 py-3 rounded-lg font-medium bg-blue-600 hover:bg-blue-700 text-white transition-colors">
              View Live Map
            </button>
            
            <button className="px-6 py-3 rounded-lg font-medium bg-gray-600 hover:bg-gray-700 text-white transition-colors">
              System Status
            </button>
          </div>
        </div>

        {/* Vehicle Fleet */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold">Fleet Overview</h2>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Vehicle
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Driver
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Route
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {vehicles.map((vehicle) => (
                    <tr key={vehicle.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <span className="text-2xl mr-3">🚐</span>
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {vehicle.registration}
                            </div>
                            <div className="text-sm text-gray-500">
                              {vehicle.type}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{vehicle.driver.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{vehicle.route.code}</div>
                        <div className="text-sm text-gray-500">{vehicle.route.name}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          vehicle.status === 'available' 
                            ? 'bg-green-100 text-green-800' 
                            : 'bg-gray-100 text-gray-800'
                        }`}>
                          {vehicle.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <button className="text-blue-600 hover:text-blue-900 mr-4">
                          Track
                        </button>
                        <button className="text-gray-600 hover:text-gray-900">
                          Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
