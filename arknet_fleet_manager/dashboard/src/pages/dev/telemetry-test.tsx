"use client";

import { useState } from 'react';
import { TelemetryProvider } from '@/core/telemetry/TelemetryContext';
import { useTelemetry } from '@/core/telemetry/useTelemetry';

interface LoginStatus {
  isLoggedIn: boolean;
  username?: string;
  tier?: string;
  jwtToken?: string;
  error?: string;
}

function TelemetryDisplay() {
  const { vehicles, connectionState, connectionType, diagnostics, error } = useTelemetry();

  // Helper to safely render error details
  const renderErrorDetails = (details: unknown): string => {
    if (typeof details === 'object' && details !== null) {
      return JSON.stringify(details, null, 2);
    }
    return String(details);
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold">
          Live Telemetry Stream ({vehicles.length} vehicles)
        </h2>
        <div className="flex items-center gap-4">
          <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
            connectionState === 'connected' ? 'bg-green-100 text-green-800' :
            connectionState === 'connecting' ? 'bg-yellow-100 text-yellow-800' :
            connectionState === 'reconnecting' ? 'bg-orange-100 text-orange-800' :
            connectionState === 'error' ? 'bg-red-100 text-red-800' :
            'bg-gray-100 text-gray-800'
          }`}>
            {connectionState === 'connected' ? '● Connected' :
             connectionState === 'connecting' ? '○ Connecting...' :
             connectionState === 'reconnecting' ? '⟳ Reconnecting...' :
             connectionState === 'error' ? '✕ Error' :
             '○ Disconnected'}
          </div>
          <div className="text-sm text-gray-600">
            via {connectionType === 'websocket' ? 'WebSocket' : 'SSE'}
          </div>
        </div>
      </div>

      {error && (() => {
        const errorCode = 'code' in error && typeof error.code === 'string' ? error.code : null;
        const errorDetails = 'details' in error && error.details ? renderErrorDetails(error.details) : null;
        
        return (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded">
            <div><strong>Error:</strong> {error.message}</div>
            {errorCode && (
              <div><strong>Code:</strong> {errorCode}</div>
            )}
            {errorDetails && (
              <details>
                <summary>Details</summary>
                <pre className="text-xs">{errorDetails}</pre>
              </details>
            )}
          </div>
        );
      })()}

      {/* Diagnostics */}
      <div className="mb-4 p-3 bg-gray-50 rounded text-xs font-mono">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          <div><strong>State:</strong> {diagnostics.state}</div>
          <div><strong>Type:</strong> {diagnostics.connectionType}</div>
          <div><strong>Reconnects:</strong> {diagnostics.reconnectAttempts}</div>
          <div><strong>WS Failures:</strong> {diagnostics.wsFailures}</div>
          <div><strong>Use SSE:</strong> {diagnostics.useSSE ? 'Yes' : 'No'}</div>
          <div><strong>Vehicles:</strong> {diagnostics.vehicleCount}</div>
        </div>
      </div>

      {/* Vehicle Data */}
      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {vehicles.length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            {connectionState === 'connected' ? 
              'Waiting for vehicle data...' : 
              'Not connected to telemetry stream'}
          </div>
        ) : (
          vehicles.map((vehicle, idx) => (
            <div
              key={typeof vehicle.vehicleId === 'string' ? vehicle.vehicleId : typeof vehicle.deviceId === 'string' ? vehicle.deviceId : String(idx)}
              className="border border-gray-200 rounded p-3 hover:bg-gray-50 transition"
            >
              <div className="font-mono text-xs">
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                  {Object.entries(vehicle).map(([key, value]) => (
                    <div key={String(key)}>
                      <span className="font-semibold text-blue-600">{key}:</span>{' '}
                      <span className="text-gray-700">
                        {typeof value === 'object' && value !== null ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function TelemetryTestContent() {
  const [loginStatus, setLoginStatus] = useState<LoginStatus>({ isLoggedIn: false });

  const users = [
    { username: 'david', password: 'Ga25w123', tier: 'admin' },
    { username: 'fleet_manager', password: 'Ga25w123', tier: 'fleet_manager' },
    { username: 'dispatcher', password: 'Ga25w123', tier: 'dispatcher' },
  ];

  const login = async (username: string, password: string) => {
    try {
      const response = await fetch('http://localhost:7000/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        setLoginStatus({
          isLoggedIn: true,
          username: data.user?.username,
          tier: data.user?.tier || 'unknown',
          jwtToken: data.jwt
        });
      } else {
        setLoginStatus({
          isLoggedIn: false,
          error: `Login failed: ${response.status}`
        });
      }
    } catch (error: unknown) {
      setLoginStatus({
        isLoggedIn: false,
        error: error instanceof Error ? error.message : 'Unknown error'
      });
    }
  };

  const logout = () => {
    setLoginStatus({ isLoggedIn: false });
  };

  if (!loginStatus.isLoggedIn) {
    return (
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Telemetry Access Test</h1>
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Login as:</h2>
            <div className="space-y-3">
              {users.map(user => (
                <button
                  key={user.username}
                  onClick={() => login(user.username, user.password)}
                  className="w-full px-4 py-3 bg-blue-600 text-white rounded hover:bg-blue-700 transition text-left"
                >
                  <div className="font-semibold">{user.username}</div>
                  <div className="text-sm opacity-90">Access Tier: {user.tier}</div>
                </button>
              ))}
            </div>
            {loginStatus.error && (
              <div className="mt-4 p-3 bg-red-100 text-red-700 rounded">
                {loginStatus.error}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <TelemetryProvider 
      baseUrl="http://localhost:5000"
      token={loginStatus.jwtToken}
    >
      <div className="min-h-screen bg-gray-50 p-8">
        <div className="max-w-6xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Telemetry Access Test</h1>

          {/* Status Bar */}
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500">Logged in as</div>
                <div className="text-xl font-semibold">{loginStatus.username}</div>
                <div className="text-sm text-gray-600">Tier: {loginStatus.tier}</div>
              </div>
              <button
                onClick={logout}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 transition text-sm"
              >
                Logout
              </button>
            </div>
          </div>

          {/* Telemetry Display */}
          <TelemetryDisplay />

          {/* Field Access Info */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h3 className="font-semibold text-blue-900 mb-2">Field Access by Tier:</h3>
            <div className="text-sm text-blue-800 space-y-1">
              <div><strong>admin:</strong> All fields (including sensitive data)</div>
              <div><strong>fleet_manager:</strong> Operational fields (excludes some internal diagnostics)</div>
              <div><strong>dispatcher:</strong> Limited fields (basic vehicle tracking only)</div>
              <div><strong>public (unauthenticated):</strong> Minimal fields (vehicle_id, route_id, location, speed)</div>
            </div>
          </div>
        </div>
      </div>
    </TelemetryProvider>
  );
}

export default function TelemetryTest() {
  return <TelemetryTestContent />;
}
