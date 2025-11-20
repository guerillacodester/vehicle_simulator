import React from 'react';
import { useTelemetry, UseTelemetryReturn } from './useTelemetry';

export type ConnectionStatus = 'connecting' | 'connected' | 'disconnected' | 'reconnecting' | 'error';

interface ConnectionStatusIndicatorProps {
  /**
   * Optionally override the connection state (for testing or custom logic)
   */
  connectionState?: ConnectionStatus;
  /**
   * Optionally show text label next to icon
   */
  showLabel?: boolean;
  /**
   * Optionally provide custom className for styling
   */
  className?: string;
}

const statusConfig: Record<ConnectionStatus, { color: string; label: string; icon: string }> = {
  connecting: { color: '#f7b500', label: 'Connecting', icon: '⏳' },
  connected: { color: '#2ecc40', label: 'Connected', icon: '🟢' },
  disconnected: { color: '#ff4136', label: 'Disconnected', icon: '🔴' },
  reconnecting: { color: '#f7b500', label: 'Reconnecting', icon: '🔄' },
  error: { color: '#ff4136', label: 'Error', icon: '⚠️' },
};

/**
 * Modular connection status indicator for telemetry connection state.
 * Can be used standalone or embedded in other components.
 * @see useTelemetry
 */
export const ConnectionStatusIndicator: React.FC<ConnectionStatusIndicatorProps> = ({
  connectionState,
  showLabel = true,
  className = '',
}) => {
  const telemetry: UseTelemetryReturn = useTelemetry();
  const state: ConnectionStatus = connectionState || telemetry.connectionState;
  const config = statusConfig[state] || statusConfig.disconnected;

  return (
    <span
      className={className}
      style={{ display: 'inline-flex', alignItems: 'center', color: config.color }}
      aria-label={`Connection status: ${config.label}`}
      title={config.label}
    >
      <span style={{ fontSize: '1.2em', marginRight: showLabel ? 6 : 0 }}>{config.icon}</span>
      {showLabel && <span>{config.label}</span>}
    </span>
  );
};

// Usage:
// <ConnectionStatusIndicator />
// <ConnectionStatusIndicator showLabel={false} />
// <ConnectionStatusIndicator connectionState="reconnecting" />
