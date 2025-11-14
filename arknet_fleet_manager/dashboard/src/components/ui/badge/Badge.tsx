import React from 'react';

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'neutral';
type BadgeSize = 'sm' | 'md' | 'lg';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  size?: BadgeSize;
  className?: string;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}: BadgeProps) {
  const sizeStyles = {
    sm: {
      padding: '0.25rem 0.5rem',
      fontSize: '0.75rem',
    },
    md: {
      padding: '0.25rem 0.75rem',
      fontSize: '0.875rem',
    },
    lg: {
      padding: '0.5rem 0.75rem',
      fontSize: '1rem',
    },
  };

  const variantStyles = {
    default: {
      backgroundColor: 'rgba(255, 255, 255, 0.1)',
      color: 'rgba(255, 255, 255, 0.9)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
    },
    success: {
      backgroundColor: 'rgba(34, 197, 94, 0.2)',
      color: '#86efac',
      border: '1px solid rgba(34, 197, 94, 0.3)',
    },
    warning: {
      backgroundColor: 'rgba(251, 191, 36, 0.2)',
      color: '#fcd34d',
      border: '1px solid rgba(251, 191, 36, 0.3)',
    },
    error: {
      backgroundColor: 'rgba(239, 68, 68, 0.2)',
      color: '#fca5a5',
      border: '1px solid rgba(239, 68, 68, 0.3)',
    },
    info: {
      backgroundColor: 'rgba(59, 130, 246, 0.2)',
      color: '#93c5fd',
      border: '1px solid rgba(59, 130, 246, 0.3)',
    },
    neutral: {
      backgroundColor: 'rgba(156, 163, 175, 0.2)',
      color: 'rgba(255, 255, 255, 0.6)',
      border: '1px solid rgba(156, 163, 175, 0.3)',
    },
  };

  const styles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '500',
    borderRadius: '9999px',
    transition: 'all 0.2s',
    ...sizeStyles[size],
    ...variantStyles[variant],
  };

  return (
    <span style={styles} className={className}>
      {children}
    </span>
  );
}
