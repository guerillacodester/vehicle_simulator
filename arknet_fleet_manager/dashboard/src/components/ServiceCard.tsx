import React from 'react';
import { Card, CardHeader, CardTitle, CardContent, Button, StatusBadge } from './ui';
import { ServiceStatus } from '@/providers/ServiceManager';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

interface ServiceCardProps {
  service: ServiceStatus;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  disabled?: boolean;
}

export function ServiceCard({ service, onStart, onStop, disabled = false }: ServiceCardProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const isRunning = service.state === 'running' || service.state === 'healthy';

  return (
    <Card hoverable>
      <CardHeader>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <CardTitle>{service.name}</CardTitle>
          <StatusBadge status={service.state} />
        </div>
      </CardHeader>
      
      <CardContent>
        <div style={{ display: 'flex', flexDirection: 'column', gap: theme.spacing.sm }}>
          {service.port && (
            <div style={{ display: 'flex', gap: theme.spacing.xs, color: t.text.secondary }}>
              <span style={{ fontWeight: '600' }}>Port:</span>
              <span>{service.port}</span>
            </div>
          )}
          
          {service.pid && (
            <div style={{ display: 'flex', gap: theme.spacing.xs, color: t.text.secondary }}>
              <span style={{ fontWeight: '600' }}>PID:</span>
              <span>{service.pid}</span>
            </div>
          )}
          
          {service.message && (
            <div style={{ 
              fontSize: '0.875rem', 
              color: t.text.tertiary,
              fontStyle: 'italic',
              marginTop: theme.spacing.sm,
            }}>
              {service.message}
            </div>
          )}
        </div>

        <div style={{ 
          display: 'flex', 
          gap: theme.spacing.sm, 
          marginTop: theme.spacing.md 
        }}>
          <Button
            variant="success"
            size="md"
            fullWidth
            onClick={() => onStart(service.name)}
            disabled={disabled || isRunning}
          >
            Start
          </Button>
          <Button
            variant="danger"
            size="md"
            fullWidth
            onClick={() => onStop(service.name)}
            disabled={disabled || !isRunning}
          >
            Stop
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
