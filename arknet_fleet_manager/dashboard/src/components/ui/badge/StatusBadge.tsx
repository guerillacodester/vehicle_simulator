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
  [ServiceState.FAILED]: {
    variant: 'error',
    label: 'FAILED',
    emoji: '🔴',
  },
};

export function StatusBadge({ status, size = 'md' }: StatusBadgeProps) {
  const config = statusConfig[status];

  return (
    <Badge variant={config.variant} size={size}>
      <span style={{ marginRight: '4px' }}>{config.emoji}</span>
      {config.label}
    </Badge>
  );
}
