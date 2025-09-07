'use client';

/**
 * CONNECTION STATUS COMPONENT
 * Shows the current connection status to the remote API
 */

import React, { useState, useEffect } from 'react';
import { dataProvider } from '@/infrastructure/data-provider';

interface ConnectionStatus {
  isConnected: boolean;
  responseTime?: number;
  error?: string;
  lastChecked?: Date;
}

export default function ConnectionStatusIndicator() {
  const [status, setStatus] = useState<ConnectionStatus>({
    isConnected: false,
    lastChecked: undefined
  });
  const [isChecking, setIsChecking] = useState(false);

  const checkConnection = async () => {
    setIsChecking(true);
    try {
      const result = await dataProvider.testConnection();
      setStatus({
        ...result,
        lastChecked: new Date()
      });
    } catch (error) {
      setStatus({
        isConnected: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        lastChecked: new Date()
      });
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    // Check connection on mount
    checkConnection();

    // Set up periodic checks every 30 seconds
    const interval = setInterval(checkConnection, 30000);

    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    if (isChecking) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    return status.isConnected 
      ? 'bg-green-100 text-green-800 border-green-300'
      : 'bg-red-100 text-red-800 border-red-300';
  };

  const getStatusIcon = () => {
    if (isChecking) return '🔄';
    return status.isConnected ? '✅' : '❌';
  };

  const getStatusText = () => {
    if (isChecking) return 'Checking...';
    if (status.isConnected) {
      return `Connected to API${status.responseTime ? ` (${status.responseTime}ms)` : ''}`;
    }
    return status.error ? `Disconnected: ${status.error}` : 'Disconnected from API';
  };

  return (
    <div className="fixed top-4 right-4 z-50">
      <div className={`flex items-center space-x-2 px-3 py-2 rounded-lg border text-sm font-medium ${getStatusColor()}`}>
        <span className={isChecking ? 'animate-spin' : ''}>{getStatusIcon()}</span>
        <span>{getStatusText()}</span>
        {!isChecking && (
          <button
            onClick={checkConnection}
            className="ml-2 text-xs underline hover:no-underline"
            title="Refresh connection status"
          >
            Refresh
          </button>
        )}
      </div>
      
      {status.lastChecked && (
        <div className="text-xs text-gray-500 text-right mt-1">
          Last checked: {status.lastChecked.toLocaleTimeString()}
        </div>
      )}
      
      {!status.isConnected && (
        <div className="mt-2 p-2 bg-yellow-50 border border-yellow-200 rounded text-xs text-yellow-800">
          <div className="font-medium">Using Mock Data</div>
          <div>API unavailable - showing sample data for development</div>
        </div>
      )}
    </div>
  );
}
