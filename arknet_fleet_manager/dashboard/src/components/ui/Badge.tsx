import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

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
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const sizeStyles = {
    sm: {
      padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
      fontSize: '0.75rem',
    },
    md: {
      padding: `${theme.spacing.xs} ${theme.spacing.md}`,
      fontSize: '0.875rem',
    },
    lg: {
      padding: `${theme.spacing.sm} ${theme.spacing.md}`,
      fontSize: '1rem',
    },
  };

  const variantStyles = {
    default: {
      backgroundColor: t.bg.tertiary,
      color: t.text.primary,
    },
    success: {
      backgroundColor: mode === 'dark' ? 'rgba(34, 197, 94, 0.2)' : '#dcfce7',
      color: mode === 'dark' ? '#86efac' : '#166534',
    },
    warning: {
      backgroundColor: mode === 'dark' ? 'rgba(251, 191, 36, 0.2)' : '#fef3c7',
      color: mode === 'dark' ? '#fcd34d' : '#92400e',
    },
    error: {
      backgroundColor: mode === 'dark' ? 'rgba(239, 68, 68, 0.2)' : '#fee2e2',
      color: mode === 'dark' ? '#fca5a5' : '#991b1b',
    },
    info: {
      backgroundColor: mode === 'dark' ? 'rgba(59, 130, 246, 0.2)' : '#dbeafe',
      color: mode === 'dark' ? '#93c5fd' : '#1e40af',
    },
    neutral: {
      backgroundColor: mode === 'dark' ? 'rgba(156, 163, 175, 0.2)' : '#f3f4f6',
      color: t.text.secondary,
    },
  };

  const styles = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: '500',
    borderRadius: theme.borderRadius.full,
    transition: `all ${theme.transitions.fast}`,
    ...sizeStyles[size],
    ...variantStyles[variant],
  };

  return (
    <span style={styles} className={className}>
      {children}
    </span>
  );
}
