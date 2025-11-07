"use client";

import { useEffect, useState } from "react";
import ServiceManager from "@/providers/ServiceManager";
import { ServiceStatus } from "@/providers/ServiceManager";
import { DashboardLayout } from "@/components/layout/DashboardLayout";
import { ServiceCard } from "@/components/features/ServiceCard";
import { Button } from "@/components/ui";
import { useTheme } from "@/contexts/ThemeContext";
import { theme } from "@/lib/theme";

export default function ServicesPage() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>([]);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const fetchStatuses = async () => {
    const result = await ServiceManager.getAllServiceStatuses();
    if (result.success && result.statuses) {
      setStatuses(result.statuses);
    }
  };

  useEffect(() => {
    const fetchData = async () => {
      await fetchStatuses();
    };
    fetchData();

    // Auto-refresh every 2 seconds if enabled
    let intervalId: NodeJS.Timeout;
    if (autoRefresh) {
      intervalId = setInterval(fetchData, 2000);
    }

    return () => {
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [autoRefresh]);

  // Subscribe to realtime events from ServiceManager (via launcher websocket)
  useEffect(() => {
    const onEvent = (status: ServiceStatus) => {
      setStatuses(prev => {
        const exists = prev.find(s => s.name === status.name);
        if (exists) {
          return prev.map(s => (s.name === status.name ? status : s));
        }
        return [...prev, status];
      });
    };

    ServiceManager.onEvent(onEvent);
    return () => {
      ServiceManager.offEvent(onEvent);
    };
  }, []);

  const handleStart = async (serviceName: string) => {
    setLoading(true);
    const result = await ServiceManager.startService(serviceName);
    if (result.success) {
      // Immediately update the UI with the new status
      if (result.status) {
        setStatuses(prev => prev.map(s => 
          s.name === serviceName ? result.status! : s
        ));
      }
    }
    await fetchStatuses();
    setLoading(false);
  };

  const handleStop = async (serviceName: string) => {
    setLoading(true);
    await ServiceManager.stopService(serviceName);
    await fetchStatuses();
    setLoading(false);
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

  const checkboxLabelStyles = {
    display: 'flex',
    alignItems: 'center',
    gap: theme.spacing.sm,
    cursor: 'pointer',
    color: t.text.secondary,
    fontSize: '0.875rem',
    userSelect: 'none' as const,
  };

  return (
    <DashboardLayout currentPath="/services">
      <div style={controlsStyles}>
        <div style={controlsContainerStyles}>
          <div style={controlsRowStyles}>
            <h2 style={titleStyles}>Services</h2>
            
            <div style={autoRefreshStyles}>
              <label style={checkboxLabelStyles}>
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  style={{ width: '16px', height: '16px', cursor: 'pointer' }}
                />
                <span style={{ fontSize: '0.875rem' }}>Auto-refresh</span>
              </label>
              
              <Button
                variant="secondary"
                size="sm"
                onClick={fetchStatuses}
                disabled={loading}
              >
                🔄 Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {statuses.length === 0 && !loading && (
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
            disabled={loading}
          />
        ))}
      </div>
    </DashboardLayout>
  );
}
