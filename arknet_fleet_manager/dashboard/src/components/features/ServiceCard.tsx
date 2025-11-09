import React from 'react';
import { StatusBadge } from '../ui';
import { ServiceStatus } from '@/providers/ServiceManager';

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
          backgroundColor: 'rgba(11, 18, 36, 0.8)',
          border: '1px solid rgba(255, 199, 38, 0.2)',
          borderRadius: '0.75rem',
          padding: '1.5rem',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
          transition: 'all 200ms ease-in-out',
          opacity: isDisconnected ? 0.6 : 1,
          pointerEvents: isDisconnected ? 'none' : 'auto',
        }}
        onMouseEnter={(e) => {
          if (!isDisconnected) {
            e.currentTarget.style.boxShadow = '0 0 20px rgba(255, 199, 38, 0.3), 0 10px 15px -3px rgba(0, 0, 0, 0.1)';
            e.currentTarget.style.borderColor = 'rgba(255, 199, 38, 0.5)';
            e.currentTarget.style.transform = 'translateY(-2px)';
          }
        }}
        onMouseLeave={(e) => {
          if (!isDisconnected) {
            e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)';
            e.currentTarget.style.borderColor = 'rgba(255, 199, 38, 0.2)';
            e.currentTarget.style.transform = 'translateY(0)';
          }
        }}
      >
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: '1rem', paddingBottom: '0.5rem', borderBottom: '1px solid rgba(255, 199, 38, 0.2)' }}>
          <div style={{ flex: 1 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
              <span style={{ fontSize: '1.25rem', lineHeight: 1 }}>{service.icon || serviceIcon}</span>
              <h3 style={{ margin: 0, fontSize: '1.125rem', fontWeight: '600', color: '#FFC726', letterSpacing: '-0.01em' }}>
                {service.display_name || service.name}
              </h3>
            </div>
            {service.description && (
              <p style={{ margin: 0, fontSize: '0.875rem', color: 'rgba(255, 255, 255, 0.7)', lineHeight: '1.4' }}>
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
              <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontWeight: '500', minWidth: '45px' }}>Port:</span>
              <code style={{ fontFamily: 'monospace', backgroundColor: 'rgba(255, 199, 38, 0.1)', color: '#FFC726', padding: '2px 8px', borderRadius: '0.375rem', fontSize: '0.8125rem', fontWeight: '500', border: '1px solid rgba(255, 199, 38, 0.3)' }}>
                {service.port}
              </code>
            </div>
          )}
          {service.pid && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem' }}>
              <span style={{ color: 'rgba(255, 255, 255, 0.6)', fontWeight: '500', minWidth: '45px' }}>PID:</span>
              <code style={{ fontFamily: 'monospace', backgroundColor: 'rgba(255, 199, 38, 0.1)', color: '#FFC726', padding: '2px 8px', borderRadius: '0.375rem', fontSize: '0.8125rem', fontWeight: '500', border: '1px solid rgba(255, 199, 38, 0.3)' }}>
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
          backgroundColor: service.message ? 'rgba(255, 199, 38, 0.1)' : 'transparent',
          borderRadius: '0.375rem',
          border: service.message ? '1px solid rgba(255, 199, 38, 0.3)' : 'none',
          marginBottom: '1rem',
          fontSize: '0.8125rem',
          color: service.message ? 'rgba(255, 255, 255, 0.8)' : 'transparent',
          lineHeight: 1.4,
          fontWeight: service.message ? '500' : '400'
        }}>
          {service.message || ''}
        </div>

        {/* Buttons - Fixed at bottom */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
          <button 
            onClick={() => onStart(service.name)} 
            disabled={disabled || isRunning} 
            style={{ 
              padding: '0.625rem 1rem',
              backgroundColor: disabled || isRunning ? 'rgba(100, 100, 100, 0.3)' : 'rgba(34, 197, 94, 0.2)', 
              color: disabled || isRunning ? 'rgba(255, 255, 255, 0.4)' : '#86efac', 
              border: disabled || isRunning ? '1px solid rgba(100, 100, 100, 0.3)' : '1px solid rgba(34, 197, 94, 0.4)',
              borderRadius: '0.5rem',
              fontWeight: '600',
              cursor: disabled || isRunning ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              fontSize: '0.875rem'
            }} 
            onMouseEnter={(e) => { 
              if (!disabled && !isRunning) { 
                e.currentTarget.style.backgroundColor = 'rgba(34, 197, 94, 0.3)';
                e.currentTarget.style.borderColor = 'rgba(34, 197, 94, 0.6)';
              } 
            }} 
            onMouseLeave={(e) => { 
              if (!disabled && !isRunning) { 
                e.currentTarget.style.backgroundColor = 'rgba(34, 197, 94, 0.2)';
                e.currentTarget.style.borderColor = 'rgba(34, 197, 94, 0.4)';
              } 
            }}
          >
            ▶ Start
          </button>
          <button 
            onClick={() => onStop(service.name)} 
            disabled={disabled || !isRunning} 
            style={{ 
              padding: '0.625rem 1rem',
              backgroundColor: disabled || !isRunning ? 'rgba(100, 100, 100, 0.3)' : 'rgba(239, 68, 68, 0.2)', 
              color: disabled || !isRunning ? 'rgba(255, 255, 255, 0.4)' : '#fca5a5', 
              border: disabled || !isRunning ? '1px solid rgba(100, 100, 100, 0.3)' : '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '0.5rem',
              fontWeight: '600',
              cursor: disabled || !isRunning ? 'not-allowed' : 'pointer',
              transition: 'all 0.2s',
              fontSize: '0.875rem'
            }} 
            onMouseEnter={(e) => { 
              if (!disabled && isRunning) { 
                e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.3)';
                e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.6)';
              } 
            }} 
            onMouseLeave={(e) => { 
              if (!disabled && isRunning) { 
                e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.2)';
                e.currentTarget.style.borderColor = 'rgba(239, 68, 68, 0.4)';
              } 
            }}
          >
            ⏹ Stop
          </button>
        </div>
      </div>
    </div>
  );
}
