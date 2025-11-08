// Placeholder for Admin Panel Page
  "use client";

  import { useEffect, useState } from "react";
  import ServiceManager, { ServiceStatus, ServiceState, ConnectionStatus, ConnectionState } from "@/providers/ServiceManager";
  import { DashboardLayout } from "@/components/layout/DashboardLayout";
  import { ServiceCard } from "@/components/features/ServiceCard";
  import { Button } from "@/components/ui";
  import { useTheme } from "@/contexts/ThemeContext";
  import { theme } from "@/lib/theme";

  export default function AdminDashboard() {
    const [statuses, setStatuses] = useState<ServiceStatus[]>([]);
    const [loadingService, setLoadingService] = useState<string | null>(null);
    const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
      state: ConnectionState.CONNECTING,
      message: 'Connecting to launcher...'
    });
    const { mode } = useTheme();
    const t = theme.colors[mode];

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
      gap: theme.spacing.sm,
      marginTop: theme.spacing.lg,
      alignItems: 'stretch',
    };

    const controlsStyles = {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      marginBottom: theme.spacing.xl,
      flexWrap: 'wrap' as const,
      gap: theme.spacing.md,
      padding: theme.spacing.lg,
      backgroundColor: t.bg.elevated,
      borderRadius: theme.borderRadius.lg,
      border: `1px solid ${t.border.default}`,
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08)',
    };

    const titleStyles = {
      fontSize: '1.5rem',
      fontWeight: '700',
      color: t.text.primary,
      margin: 0,
      background: `linear-gradient(135deg, ${t.interactive.primary.default}, ${t.interactive.accent.default})`,
      WebkitBackgroundClip: 'text',
      WebkitTextFillColor: 'transparent',
      backgroundClip: 'text',
    };

    const controlsContainerStyles = {
      display: 'flex',
      flexDirection: 'column' as const,
      gap: theme.spacing.md,
      width: '100%',
    };

    const controlsRowStyles = {
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      flexWrap: 'wrap' as const,
      gap: theme.spacing.md,
    };

    const autoRefreshStyles = {
      display: 'flex',
      alignItems: 'center',
      gap: theme.spacing.md,
    };

    return (
      <DashboardLayout currentPath="/admin">
        <div style={controlsStyles}>
          <div style={controlsContainerStyles}>
            <div style={controlsRowStyles}>
              <h2 style={titleStyles}>Services</h2>
              <div style={autoRefreshStyles}>
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: theme.spacing.sm, 
                  marginBottom: theme.spacing.xs,
                  padding: theme.spacing.sm,
                  backgroundColor: 
                    connectionStatus.state === ConnectionState.CONNECTED ? 'rgba(16, 185, 129, 0.1)' :
                    connectionStatus.state === ConnectionState.CONNECTING ? 'rgba(245, 158, 11, 0.1)' :
                    connectionStatus.state === ConnectionState.DISCONNECTED ? 'rgba(239, 68, 68, 0.1)' :
                    'rgba(239, 68, 68, 0.1)',
                  borderRadius: theme.borderRadius.md,
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
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={fetchStatuses}
                  disabled={loadingService !== null || connectionStatus.state !== ConnectionState.CONNECTED}
                >
                  🔄 Refresh
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReloadServices}
                  disabled={loadingService === 'reloading' || connectionStatus.state !== ConnectionState.CONNECTED}
                >
                  {loadingService === 'reloading' ? '⏳' : '🔃'} Reload Services
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleReloadConfig}
                  disabled={loadingService !== null}
                >
                  ⚙️ Reload Config
                </Button>
              </div>
            </div>
          </div>
        </div>
        {statuses.length === 0 && loadingService === null && (
          <div style={{
            textAlign: 'center',
            backgroundColor: t.bg.elevated,
            border: `2px dashed ${t.border.default}`,
            borderRadius: theme.borderRadius.lg,
            padding: theme.spacing.xl,
          }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: theme.spacing.md,
              color: t.text.secondary,
            }}>
              <div style={{ fontSize: '3rem', opacity: 0.5 }}>⚙️</div>
              <div>
                <h3 style={{
                  fontSize: '1.25rem',
                  fontWeight: '600',
                  color: t.text.primary,
                  margin: 0,
                  marginBottom: theme.spacing.sm
                }}>
                  No Services Found
                </h3>
                <p style={{
                  fontSize: '0.875rem',
                  margin: 0,
                  color: t.text.tertiary
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