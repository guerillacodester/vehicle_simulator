import React from 'react';
import { useTheme } from '@/contexts/ThemeContext';
import { theme } from '@/lib/theme';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  padding?: 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  onClick?: () => void;
}

export function Card({
  children,
  className = '',
  padding = 'md',
  hoverable = false,
  onClick,
}: CardProps) {
  const { mode } = useTheme();
  const t = theme.colors[mode];

  const paddingMap = {
    sm: theme.spacing.md,
    md: theme.spacing.lg,
    lg: theme.spacing.xl,
  };

  const styles = {
    backgroundColor: t.bg.secondary,
    border: `1px solid ${t.border.default}`,
    borderRadius: theme.borderRadius.lg,
    padding: paddingMap[padding],
    boxShadow: theme.shadows.sm,
    transition: `all ${theme.transitions.normal}`,
    cursor: onClick ? 'pointer' : 'default',
    ...(hoverable && {
      ':hover': {
        boxShadow: theme.shadows.md,
        borderColor: t.border.hover,
        transform: 'translateY(-2px)',
      },
    }),
  };

  return (
    <div style={styles} className={className} onClick={onClick}>
      {children}
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
