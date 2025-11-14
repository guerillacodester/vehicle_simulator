"use client";

import { useEffect, useState } from "react";
import ServiceManager, { ServiceStatus, ServiceState, ConnectionStatus, ConnectionState } from "@/providers/ServiceManager";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ServiceCard } from "@/components/features/ServiceCard";

export default function ServicesPage() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>([]);
  const [loadingService, setLoadingService] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    state: ConnectionState.CONNECTING,
    message: 'Connecting to launcher...'
  });

  const fetchStatuses = async () => {
    const result = await ServiceManager.getAllServiceStatuses();
    if (result.success && result.statuses) {
      setStatuses(result.statuses);
    }
  };

  const handleReloadServices = async () => {
    setLoadingService('reloading');
    await ServiceManager.reloadServices();
    await fetchStatuses();
    setLoadingService(null);
  };

  useEffect(() => {
    const fetchData = async () => {
      // Initial load only - fetch statuses once on component mount
      await fetchStatuses();
    };
    fetchData();

    // Subscribe to real-time service status updates
    const onServiceEvent = (status: ServiceStatus) => {
      setStatuses(prev => {
        // Update the matching service, or add if not present
        const found = prev.find(s => s.name === status.name);
        if (found) {
          return prev.map(s => s.name === status.name ? { ...s, ...status } : s);
        } else {
          return [...prev, status];
        }
      });
    };
    ServiceManager.onEvent(onServiceEvent);

    return () => {
      ServiceManager.offEvent(onServiceEvent);
    };
  }, []); // Empty dependency array - only run once on mount

  // Subscribe to connection status events
  useEffect(() => {
    const onConnectionEvent = (status: ConnectionStatus) => {
      setConnectionStatus(status);
    };
    
    ServiceManager.onConnectionEvent(onConnectionEvent);
    
    return () => {
      ServiceManager.offConnectionEvent(onConnectionEvent);
    };
  }, []);

  const handleStart = async (serviceName: string) => {
    setLoadingService(serviceName);
    
    // Immediately set status to starting
    setStatuses(prev => prev.map(s => 
      s.name === serviceName ? { ...s, state: ServiceState.STARTING, message: 'Starting service...' } : s
    ));
    
    try {
      const result = await ServiceManager.startService(serviceName);
      if (!result.success) {
        // Update status on failure
        setStatuses(prev => prev.map(s => 
          s.name === serviceName ? { ...s, state: ServiceState.FAILED, message: result.message } : s
        ));
      }
      // Success updates come via WebSocket
    } finally {
      setLoadingService(null);
    }
  };

  const handleStop = async (serviceName: string) => {
    setLoadingService(serviceName);
    
    // Immediately set status to stopping
    setStatuses(prev => prev.map(s => 
      s.name === serviceName ? { ...s, message: 'Stopping service...' } : s
    ));
    
    try {
      await ServiceManager.stopService(serviceName);
      // Status updates come via WebSocket
    } finally {
      setLoadingService(null);
    }
  };

  const handleReloadConfig = async () => {
    setLoadingService('config');
    
    try {
      const result = await ServiceManager.reloadConfig();
      if (result.success) {
        // Refresh statuses after config reload
        await fetchStatuses();
      } else {
        console.error('Failed to reload config:', result.message);
        // Could add a toast notification here
      }
    } finally {
      setLoadingService(null);
    }
  };

  const gridStyles = {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
    gap: '1rem',
    marginTop: '2rem',
    alignItems: 'stretch',
  };

  const controlsStyles = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '2rem',
    flexWrap: 'wrap' as const,
    gap: '1rem',
    padding: '1.5rem',
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    borderRadius: '12px',
    border: '1px solid rgba(255, 199, 38, 0.2)',
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08)',
  };

  const titleStyles = {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#FFC726',
    margin: 0,
    background: 'linear-gradient(135deg, #FFC726, #FFD54F)',
    WebkitBackgroundClip: 'text',
    WebkitTextFillColor: 'transparent',
    backgroundClip: 'text',
  };

  const controlsContainerStyles = {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '1rem',
    width: '100%',
  };

  const controlsRowStyles = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap' as const,
    gap: '1rem',
  };

  const autoRefreshStyles = {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  };

  return (
    <DashboardLayout currentPath="/services">
      <div style={controlsStyles}>
        <div style={controlsContainerStyles}>
          <div style={controlsRowStyles}>
            <h2 style={titleStyles}>Services</h2>
            
            <div style={autoRefreshStyles}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'center', 
                gap: '0.5rem', 
                marginBottom: '0.25rem',
                padding: '0.5rem',
                backgroundColor: 
                  connectionStatus.state === ConnectionState.CONNECTED ? 'rgba(16, 185, 129, 0.1)' :
                  connectionStatus.state === ConnectionState.CONNECTING ? 'rgba(245, 158, 11, 0.1)' :
                  connectionStatus.state === ConnectionState.DISCONNECTED ? 'rgba(239, 68, 68, 0.1)' :
                  'rgba(239, 68, 68, 0.1)',
                borderRadius: '8px',
                border: `1px solid ${
                  connectionStatus.state === ConnectionState.CONNECTED ? 'rgba(16, 185, 129, 0.3)' :
                  connectionStatus.state === ConnectionState.CONNECTING ? 'rgba(245, 158, 11, 0.3)' :
                  connectionStatus.state === ConnectionState.DISCONNECTED ? 'rgba(239, 68, 68, 0.3)' :
                  'rgba(239, 68, 68, 0.3)'
                }`
              }}>
                <div style={{
                  width: '8px',
                  height: '8px',
                  borderRadius: '50%',
                  backgroundColor: 
                    connectionStatus.state === ConnectionState.CONNECTED ? '#10b981' :
                    connectionStatus.state === ConnectionState.CONNECTING ? '#f59e0b' :
                    connectionStatus.state === ConnectionState.DISCONNECTED ? '#ef4444' :
                    '#ef4444',
                  animation: connectionStatus.state === ConnectionState.CONNECTING ? 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite' : 'none'
                }} />
                <span style={{ 
                  fontSize: '0.875rem', 
                  fontWeight: '500',
                  color: 
                    connectionStatus.state === ConnectionState.CONNECTED ? '#10b981' :
                    connectionStatus.state === ConnectionState.CONNECTING ? '#f59e0b' :
                    connectionStatus.state === ConnectionState.DISCONNECTED ? '#ef4444' :
                    '#ef4444'
                }}>
                  {connectionStatus.message}
                </span>
              </div>
              
              <button
                onClick={fetchStatuses}
                disabled={loadingService !== null || connectionStatus.state !== ConnectionState.CONNECTED}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'rgba(255, 199, 38, 0.1)',
                  border: '1px solid rgba(255, 199, 38, 0.3)',
                  borderRadius: '8px',
                  color: '#FFC726',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: loadingService !== null || connectionStatus.state !== ConnectionState.CONNECTED ? 'not-allowed' : 'pointer',
                  opacity: loadingService !== null || connectionStatus.state !== ConnectionState.CONNECTED ? 0.5 : 1,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (loadingService === null && connectionStatus.state === ConnectionState.CONNECTED) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 199, 38, 0.2)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 199, 38, 0.1)';
                }}
              >
                🔄 Refresh
              </button>
              
              <button
                onClick={handleReloadServices}
                disabled={loadingService === 'reloading' || connectionStatus.state !== ConnectionState.CONNECTED}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: loadingService === 'reloading' || connectionStatus.state !== ConnectionState.CONNECTED ? 'not-allowed' : 'pointer',
                  opacity: loadingService === 'reloading' || connectionStatus.state !== ConnectionState.CONNECTED ? 0.5 : 1,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (loadingService !== 'reloading' && connectionStatus.state === ConnectionState.CONNECTED) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }}
              >
                {loadingService === 'reloading' ? '⏳' : '🔃'} Reload Services
              </button>
              
              <button
                onClick={handleReloadConfig}
                disabled={loadingService !== null}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'rgba(255, 255, 255, 0.05)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '8px',
                  color: 'rgba(255, 255, 255, 0.7)',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  cursor: loadingService !== null ? 'not-allowed' : 'pointer',
                  opacity: loadingService !== null ? 0.5 : 1,
                  transition: 'all 0.2s',
                }}
                onMouseEnter={(e) => {
                  if (loadingService === null) {
                    e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.1)';
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.05)';
                }}
              >
                ⚙️ Reload Config
              </button>
            </div>
          </div>
        </div>
      </div>

      {statuses.length === 0 && loadingService === null && (
        <div style={{
          textAlign: 'center',
          backgroundColor: 'rgba(255, 255, 255, 0.05)',
          border: '2px dashed rgba(255, 199, 38, 0.2)',
          borderRadius: '12px',
          padding: '2rem',
        }}>
          <div style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '1rem',
            color: 'rgba(255, 255, 255, 0.6)',
          }}>
            <div style={{ fontSize: '3rem', opacity: 0.5 }}>⚙️</div>
            <div>
              <h3 style={{
                fontSize: '1.25rem',
                fontWeight: '600',
                color: '#FFC726',
                margin: 0,
                marginBottom: '0.5rem'
              }}>
                No Services Found
              </h3>
              <p style={{
                fontSize: '0.875rem',
                margin: 0,
                color: 'rgba(255, 255, 255, 0.4)'
              }}>
                Make sure the launcher is running on port 7000 to see available services.
              </p>
            </div>
          </div>
        </div>
      )}

      <div style={gridStyles}>
        {statuses.map((service) => (
          <ServiceCard
            key={service.name}
            service={service}
            onStart={handleStart}
            onStop={handleStop}
            disabled={loadingService === service.name}
            isDisconnected={connectionStatus.state !== ConnectionState.CONNECTED}
          />
        ))}
      </div>
    </DashboardLayout>
  );
}
