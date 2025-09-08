'use client';

/**
 * CONNECTION STATUS COMPONENT
 * Shows real-time connection status using Socket.io
 */

import React, { useState, useEffect } from 'react';
import { socketConnectionService, ConnectionStatus as SocketConnectionStatus } from '@/services/socket-connection';
import { Wifi, WifiOff, Clock, AlertCircle, Activity } from 'lucide-react';

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
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    // Initialize socket connection
    socketConnectionService.connect();

    // Subscribe to real-time status updates
    const unsubscribe = socketConnectionService.onStatusChange((newStatus: SocketConnectionStatus) => {
      setStatus(newStatus);
    });

    // Ping every 10 seconds to measure latency
    const pingInterval = setInterval(() => {
      socketConnectionService.ping();
    }, 10000);

    // Cleanup on unmount
    return () => {
      unsubscribe();
      clearInterval(pingInterval);
      // Note: We don't disconnect the socket here as other components might be using it
    };
  }, []);

  if (!isVisible) return null;

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`connection-status ${status.isConnected ? 'connected' : 'disconnected'}`}>
      <div className="connection-content">
        <div className="status-icon">
          {status.isConnected ? (
            <Wifi size={16} />
          ) : (
            <WifiOff size={16} />
          )}
        </div>
        
        <div className="status-text">
          <span className="status-label">
            {status.isConnected ? 'Connected' : 'Disconnected'}
          </span>
          {status.responseTime && (
            <span className="response-time">{status.responseTime}ms</span>
          )}
          {status.lastChecked && (
            <span className="last-checked">
              Last: {formatTime(status.lastChecked)}
            </span>
          )}
        </div>

        {status.error && (
          <div className="error-indicator" title={status.error}>
            <AlertCircle size={14} />
          </div>
        )}
      </div>
      
      <button 
        onClick={() => setIsVisible(false)} 
        className="dismiss-button"
        title="Hide connection status"
      >
        ×
      </button>
    </div>
  );
}
