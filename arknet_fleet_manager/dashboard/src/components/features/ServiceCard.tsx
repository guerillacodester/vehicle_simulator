import React from 'react';
import { StatusBadge } from '../ui';
import { ServiceStatus } from '@/providers/ServiceManager';
import { colors, shadows } from '@/lib/cssVars';

interface ServiceCardProps {
  service: ServiceStatus;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
  disabled?: boolean;
  isDisconnected?: boolean;
}

export function ServiceCard({ service, onStart, onStop, disabled = false, isDisconnected = false }: ServiceCardProps) {
  const isRunning = service.state === 'running' || service.state === 'healthy';

  const serviceIcon = {
    running: '🟢',
    healthy: '🟢',
    starting: '🟡',
    stopped: '⚪',
    failed: '🔴',
    unhealthy: '🟠',
  }[service.state] || '⚪';

  return (
    <div style={{ position: 'relative', height: '280px' }}>
      {isDisconnected && (
        <div style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.05)',
          backdropFilter: 'blur(1px)',
          borderRadius: '0.75rem',
          zIndex: 1,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          pointerEvents: 'none',
        }}>
          <div style={{
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '0.5rem 1rem',
            borderRadius: '0.5rem',
            fontSize: '0.875rem',
            fontWeight: '500',
          }}>
            🔌 Disconnected
          </div>
        </div>
      )}
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
          opacity: isDisconnected ? 0.6 : 1,
          pointerEvents: isDisconnected ? 'none' : 'auto',
        }}
        onMouseEnter={(e) => {
          if (!isDisconnected) {
            e.currentTarget.style.boxShadow = shadows.cardHover;
            e.currentTarget.style.borderColor = colors.border.hover;
            e.currentTarget.style.transform = 'translateY(-2px)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isDisconnected) {
            e.currentTarget.style.boxShadow = shadows.card;
            e.currentTarget.style.borderColor = colors.border.default;
            e.currentTarget.style.transform = 'translateY(0)';
          }
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: `1px solid ${colors.border.subtle}` }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '1.25rem', lineHeight: 1 }}>{service.icon || serviceIcon}</span>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: colors.text.primary, letterSpacing: '-0.01em' }}>
                {service.display_name || service.name}
              </h3>
            </div>
            {service.description && (
              <p style={{ margin: 0, fontSize: '0.875rem', color: colors.text.secondary, lineHeight: '1.4' }}>
                {service.description}
              </p>
            )}
          </div>
          <StatusBadge status={service.state} size="sm" />
        </div>

        {/* Main Content - Flexible */}
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
        </div>

        {/* Status Bar - Always visible, fixed height */}
        <div style={{
          height: '3rem',
          display: 'flex',
          alignItems: 'center',
          padding: '0.5rem',
          backgroundColor: service.message ? colors.bg.tertiary : 'transparent',
          borderRadius: '0.375rem',
          border: service.message ? `1px solid ${colors.border.subtle}` : 'none',
          marginBottom: '1rem',
          fontSize: '0.8125rem',
          color: service.message ? colors.text.tertiary : 'transparent',
          lineHeight: 1.4,
          fontWeight: service.message ? '500' : '400'
        }}>
          {service.message || ''}
        </div>

        {/* Buttons - Fixed at bottom */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
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
