import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  onClick?: () => void;
  compact?: boolean;
  fixedHeight?: string;
}

export function Card({
  children,
  className = '',
  padding = 'md',
  hoverable = false,
  onClick,
  compact = false,
  fixedHeight,
}: CardProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const paddingMap = {
    sm: compact ? theme.spacing.sm : theme.spacing.md,
    md: compact ? theme.spacing.md : theme.spacing.lg,
    lg: compact ? theme.spacing.lg : theme.spacing.xl,
  };

  const baseStyles: React.CSSProperties = {
    backgroundColor: t.bg.card,
    border: `1px solid ${t.border.default}`,
    borderRadius: theme.borderRadius.lg,
    padding: paddingMap[padding],
    boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1), 0 1px 3px rgba(0, 0, 0, 0.08)',
    transition: `all ${theme.transitions.normal}`,
    cursor: onClick ? 'pointer' : 'default',
    position: 'relative',
    overflow: 'hidden',
    ...(fixedHeight && { height: fixedHeight, display: 'flex', flexDirection: 'column' }),
  };

  return (
    <div
      style={baseStyles}
      className={`${className} ${hoverable ? 'hoverable-card' : ''}`}
      onClick={onClick}
    >
      {children}
      <style jsx>{`
        .hoverable-card {
          transition: all ${theme.transitions.normal};
        }
        .hoverable-card:hover {
          box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15), 0 4px 12px rgba(0, 0, 0, 0.12) !important;
          border-color: ${t.border.hover} !important;
          transform: translateY(-4px) scale(1.02);
          background-color: ${t.bg.elevated} !important;
        }
        .hoverable-card:active {
          transform: translateY(-2px) scale(1.01);
          box-shadow: 0 4px 15px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.1);
        }
      `}</style>
    </div>
  );
}

interface CardHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export function CardHeader({ children, className = '' }: CardHeaderProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const styles = {
    marginBottom: theme.spacing.md,
    paddingBottom: theme.spacing.md,
    borderBottom: `1px solid ${t.border.subtle}`,
  };

  return (
    <div style={styles} className={className}>
      {children}
    </div>
  );
}

interface CardTitleProps {
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export function CardTitle({ children, className = '', style }: CardTitleProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const baseStyles = {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: t.text.primary,
    margin: 0,
  };

  const combinedStyles = { ...baseStyles, ...style };

  return (
    <h3 style={combinedStyles} className={className}>
      {children}
    </h3>
  );
}

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export function CardContent({ children, className = '' }: CardContentProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const styles = {
    color: t.text.secondary,
  };

  return (
    <div style={styles} className={className}>
      {children}
    </div>
  );
}
