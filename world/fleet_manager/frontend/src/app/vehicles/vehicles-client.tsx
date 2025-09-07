'use client';

/**
 * VEHICLES CLIENT COMPONENT - Vehicle Management Interface
 * Client-side component fo                      <div className="flex items-center">
                        <div className="flex-shrink-0">
                          <div className="h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center">
                            <span className="text-white font-bold text-sm">
                              {(vehicle.plateNumber || vehicle.regCode || 'UK').substring(0, 2)}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <h3 className="text-lg font-medium text-gray-900">
                            {vehicle.plateNumber || vehicle.regCode || 'Unknown'}
                          </h3>
                          <p className="text-sm text-gray-500">{vehicle.model || 'Vehicle'}</p>
                        </div>
                      </div>operations
 */

import React, { useState, useEffect } from 'react';
import { Vehicle, VehicleStatus } from '@/domain/entities';
import { VehicleUseCases } from '@/application/use-cases';
import { FleetManagementApp } from '@/app';

export default function VehiclesClient() {
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Initialize the application
  const [app] = useState(() => new FleetManagementApp());
  const [vehicleUseCases] = useState(() => app.getVehicleUseCases());

  useEffect(() => {
    loadVehicles();
  }, []);

  const loadVehicles = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedVehicles = await vehicleUseCases.getAllVehicles();
      setVehicles(fetchedVehicles);
    } catch (err) {
      console.error('Error loading vehicles:', err);
      setError(err instanceof Error ? err.message : 'Failed to load vehicles');
    } finally {
      setLoading(false);
    }
  };

  const getStatusBadgeColor = (status?: VehicleStatus): string => {
    switch (status) {
      case VehicleStatus.ACTIVE:
        return 'bg-green-100 text-green-800';
      case VehicleStatus.MAINTENANCE:
        return 'bg-yellow-100 text-yellow-800';
      case VehicleStatus.OUT_OF_SERVICE:
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading vehicles...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded">
            <strong className="font-bold">Error!</strong>
            <span className="block sm:inline"> {error}</span>
          </div>
          <button
            onClick={loadVehicles}
            className="mt-4 bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="px-4 py-6 sm:px-0">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Fleet Vehicles</h1>
              <p className="mt-2 text-sm text-gray-600">
                Manage your fleet vehicles, track status, and view details
              </p>
            </div>
            <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg">
              Add Vehicle
            </button>
          </div>
        </div>

        {/* Vehicles Grid */}
        <div className="px-4 sm:px-0">
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {vehicles.map((vehicle) => (
              <div
                key={vehicle.id}
                className="bg-white overflow-hidden shadow rounded-lg border border-gray-200 hover:shadow-md transition-shadow"
              >
                <div className="p-6">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center">
                      <div className="flex-shrink-0">
                        <div className="h-10 w-10 bg-blue-500 rounded-full flex items-center justify-center">
                          <span className="text-white font-bold text-sm">
                            {vehicle.plateNumber.substring(0, 2)}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <h3 className="text-lg font-medium text-gray-900">
                          {vehicle.plateNumber}
                        </h3>
                        <p className="text-sm text-gray-500">{vehicle.model}</p>
                      </div>
                    </div>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeColor(
                        vehicle.status
                      )}`}
                    >
                      {vehicle.status || 'Unknown'}
                    </span>
                  </div>

                  <div className="mt-4">
                    <dl className="grid grid-cols-2 gap-x-4 gap-y-2 text-sm">
                      <div>
                        <dt className="font-medium text-gray-500">Reg Code</dt>
                        <dd className="text-gray-900">{vehicle.regCode}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-gray-500">Capacity</dt>
                        <dd className="text-gray-900">{vehicle.capacity > 0 ? `${vehicle.capacity} passengers` : 'Not specified'}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-gray-500">Depot</dt>
                        <dd className="text-gray-900">{vehicle.depotId || 'Not assigned'}</dd>
                      </div>
                      <div>
                        <dt className="font-medium text-gray-500">Country</dt>
                        <dd className="text-gray-900">{vehicle.countryId}</dd>
                      </div>
                    </dl>
                  </div>

                  <div className="mt-6 flex space-x-3">
                    <button className="flex-1 bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 font-medium py-2 px-3 rounded-md text-sm">
                      Edit
                    </button>
                    <button className="flex-1 bg-blue-600 text-white hover:bg-blue-700 font-medium py-2 px-3 rounded-md text-sm">
                      View Details
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {vehicles.length === 0 && !loading && (
            <div className="text-center py-12">
              <div className="h-12 w-12 mx-auto bg-gray-100 rounded-full flex items-center justify-center">
                <span className="text-gray-400 text-xl">🚐</span>
              </div>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No vehicles</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by adding your first vehicle.
              </p>
              <div className="mt-6">
                <button className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded-lg">
                  Add Vehicle
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
