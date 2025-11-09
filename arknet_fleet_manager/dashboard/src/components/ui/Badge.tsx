import React from 'react';
// Badge uses static arknet-like colors to avoid ThemeProvider dependency

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
    sm: { padding: '0.125rem 0.5rem', fontSize: '0.75rem' },
    md: { padding: '0.25rem 0.75rem', fontSize: '0.875rem' },
    lg: { padding: '0.5rem 0.75rem', fontSize: '1rem' },
  };

  const variantStyles: Record<string, React.CSSProperties> = {
    default: { backgroundColor: 'rgba(255,255,255,0.03)', color: '#ffffff' },
    success: { backgroundColor: 'rgba(34,197,94,0.12)', color: '#86efac' },
    warning: { backgroundColor: 'rgba(252,211,77,0.12)', color: '#f59e0b' },
    error: { backgroundColor: 'rgba(239,68,68,0.12)', color: '#f87171' },
    info: { backgroundColor: 'rgba(59,130,246,0.12)', color: '#93c5fd' },
    neutral: { backgroundColor: 'rgba(156,163,175,0.08)', color: '#cbd5e1' },
  };

  const styles: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 500,
    borderRadius: '9999px',
    transition: 'all 120ms ease',
    ...sizeStyles[size],
    ...variantStyles[variant],
  };

  return (
    <span style={styles} className={className}>
      {children}
    </span>
  );
}
