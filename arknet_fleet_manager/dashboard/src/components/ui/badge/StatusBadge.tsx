import React from 'react';
import { Badge } from './Badge';
import { ServiceState } from '@/providers/ServiceManager';

interface StatusBadgeProps {
  status: ServiceState;
  size?: 'sm' | 'md' | 'lg';
}

const statusConfig: Record<ServiceState, { variant: 'default' | 'success' | 'warning' | 'error' | 'info' | 'neutral', label: string, emoji: string }> = {
  [ServiceState.STOPPED]: {
    variant: 'neutral',
    label: 'STOPPED',
    emoji: '⚪',
  },
  [ServiceState.STARTING]: {
    variant: 'warning',
    label: 'STARTING',
    emoji: '🟡',
  },
  [ServiceState.RUNNING]: {
    variant: 'info',
    label: 'RUNNING',
    emoji: '🔵',
  },
  [ServiceState.HEALTHY]: {
    variant: 'success',
    label: 'HEALTHY',
    emoji: '🟢',
  },
  [ServiceState.UNHEALTHY]: {
    variant: 'error',
    label: 'UNHEALTHY',
    emoji: '🟠',
  },
  [ServiceState.FAILED]: {
    variant: 'error',
    label: 'FAILED',
    emoji: '🔴',
  },
  [ServiceState.NOT_CONFIGURED]: {
    variant: 'neutral',
    label: 'NOT CONFIGURED',
    emoji: '⚙️',
  },
  [ServiceState.UNREACHABLE]: {
    variant: 'error',
    label: 'UNREACHABLE',
    emoji: '❌',
  },
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status];

  // Handle unknown status values
  if (!config) {
    return (
      <Badge variant="neutral" size={size}>
        <span style={{ marginRight: '4px' }}>⚪</span>
        {String(status).toUpperCase()}
      </Badge>
    );
  }

  return (
    <Badge variant={config.variant} size={size}>
      <span style={{ marginRight: '4px' }}>{config.emoji}</span>
      {config.label}
    </Badge>
  );
}
