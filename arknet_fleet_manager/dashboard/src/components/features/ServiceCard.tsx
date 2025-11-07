import React from 'react';
import { StatusBadge } from '../ui';
import { ServiceStatus } from '@/providers/ServiceManager';
import { colors, shadows } from '@/lib/cssVars';

interface ServiceCardProps {
  service: ServiceStatus;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  disabled?: boolean;
}

export function ServiceCard({ service, onStart, onStop, disabled = false }: ServiceCardProps) {
  const isRunning = service.state === 'running' || service.state === 'healthy';

  const serviceIcon = {
    running: '🟢',
    healthy: '🟢',
    starting: '🟡',
    stopped: '⚪',
    failed: '🔴',
  }[service.state] || '⚪';

  return (
    <div style={{ position: 'relative', height: '100%', minHeight: '220px' }}>
      <div
        style={{
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          backgroundColor: colors.bg.card,
          border: `1px solid ${colors.border.default}`,
          borderRadius: '0.75rem',
          padding: '1.5rem',
          boxShadow: shadows.card,
          transition: 'all 200ms ease-in-out',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.boxShadow = shadows.cardHover;
          e.currentTarget.style.borderColor = colors.border.hover;
          e.currentTarget.style.transform = 'translateY(-2px)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.boxShadow = shadows.card;
          e.currentTarget.style.borderColor = colors.border.default;
          e.currentTarget.style.transform = 'translateY(0)';
        }}
      >
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: `1px solid ${colors.border.subtle}` }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '1.25rem', lineHeight: 1 }}>{serviceIcon}</span>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: colors.text.primary, letterSpacing: '-0.01em' }}>
                {service.name}
              </h3>
            </div>
          </div>
          <StatusBadge status={service.state} size="sm" />
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem', marginBottom: '1rem' }}>
          {service.port && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <span style={{ color: colors.text.secondary, fontWeight: '500', minWidth: '45px' }}>Port:</span>
              <code style={{ fontFamily: 'monospace', backgroundColor: colors.bg.tertiary, color: colors.text.primary, padding: '2px 8px', borderRadius: '0.375rem', fontSize: '0.8125rem', fontWeight: '500', border: `1px solid ${colors.border.subtle}` }}>
                {service.port}
              </code>
            </div>
          )}
          {service.pid && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <span style={{ color: colors.text.secondary, fontWeight: '500', minWidth: '45px' }}>PID:</span>
              <code style={{ fontFamily: 'monospace', backgroundColor: colors.bg.tertiary, color: colors.text.primary, padding: '2px 8px', borderRadius: '0.375rem', fontSize: '0.8125rem', fontWeight: '500', border: `1px solid ${colors.border.subtle}` }}>
                {service.pid}
              </code>
            </div>
          )}
          {service.message && (
            <div style={{ fontSize: '0.8125rem', color: colors.text.tertiary, padding: '0.5rem', backgroundColor: colors.bg.tertiary, borderRadius: '0.5rem', border: `1px solid ${colors.border.subtle}`, lineHeight: 1.5 }}>
              {service.message}
            </div>
          )}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', paddingTop: '0.5rem', borderTop: `1px solid ${colors.border.subtle}` }}>
          <button onClick={() => onStart(service.name)} disabled={disabled || isRunning} className="btn btn-success" style={{ backgroundColor: disabled || isRunning ? colors.disabled.bg : colors.status.success, color: disabled || isRunning ? colors.disabled.text : '#ffffff', opacity: disabled || isRunning ? 0.5 : 1, boxShadow: disabled || isRunning ? 'none' : shadows.button }} onMouseEnter={(e) => { if (!disabled && !isRunning) { e.currentTarget.style.backgroundColor = colors.status.successHover; } }} onMouseLeave={(e) => { if (!disabled && !isRunning) { e.currentTarget.style.backgroundColor = colors.status.success; } }}>
            <span></span> Start
          </button>
          <button onClick={() => onStop(service.name)} disabled={disabled || !isRunning} className="btn btn-error" style={{ backgroundColor: disabled || !isRunning ? colors.disabled.bg : colors.status.error, color: disabled || !isRunning ? colors.disabled.text : '#ffffff', opacity: disabled || !isRunning ? 0.5 : 1, boxShadow: disabled || !isRunning ? 'none' : shadows.button }} onMouseEnter={(e) => { if (!disabled && isRunning) { e.currentTarget.style.backgroundColor = colors.status.errorHover; } }} onMouseLeave={(e) => { if (!disabled && isRunning) { e.currentTarget.style.backgroundColor = colors.status.error; } }}>
            <span></span> Stop
          </button>
        </div>
      </div>
    </div>
  );
}
